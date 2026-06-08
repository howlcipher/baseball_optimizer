from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:////run/media/system/tallgeese/dev/baseball_optimizer/baseball_optimizer.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)  # MLB standard ID
    name = Column(String, nullable=False)
    location_abbr = Column(String(10), nullable=False)
    stadium_name = Column(String, nullable=False)
    elevation = Column(Float, nullable=False)  # altitude in feet
    base_park_factor = Column(Float, default=1.0)

    environmental_context = relationship("EnvironmentalContext", back_populates="team", uselist=False, cascade="all, delete-orphan")
    managerial_override = relationship("ManagerialOverride", back_populates="team", uselist=False, cascade="all, delete-orphan")
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")


class EnvironmentalContext(Base):
    __tablename__ = "environmental_contexts"

    game_id = Column(String, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    temperature = Column(Float, nullable=False)  # Fahrenheit
    humidity = Column(Float, nullable=False)  # Percentage
    wind_velocity = Column(Float, nullable=False)  # mph
    wind_direction = Column(String, nullable=False)  # "In", "Out", "Cross-Left", "Cross-Right"

    team = relationship("Team", back_populates="environmental_context")


class ManagerialOverride(Base):
    __tablename__ = "managerial_overrides"

    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    fatigue_threshold = Column(Integer, default=5)  # consecutive days played before tax
    clutch_weight = Column(Float, default=1.0)
    defensive_sub_inning = Column(Integer, default=7)
    cold_bench_friction_tax = Column(Float, default=0.15)  # pinch hitter penalty

    team = relationship("Team", back_populates="managerial_override")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)  # MLB Player ID or custom
    name = Column(String, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    position = Column(String, nullable=False)  # "P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"
    cumulative_days_played = Column(Integer, default=0)
    disrupted_sleep_hours = Column(Float, default=0.0)
    leverage_anxiety_modifier = Column(Float, default=0.0)  # standard anxiety penalty (e.g. -0.05)
    batting_handedness = Column(String(1), default="R")  # "L", "R", "S"
    
    # Base Sabermetric metrics
    base_obp = Column(Float, default=0.320)
    base_slg = Column(Float, default=0.400)
    base_ops = Column(Float, default=0.720)  # Primary metric we use for core calculations

    # Physical swing and bat parameters
    typical_swing_angle = Column(Float, default=15.0)
    bat_swing_speed = Column(Float, default=72.0)
    choke_up = Column(Integer, default=0)  # 0 or 1
    bat_size = Column(Float, default=33.0)
    bat_weight = Column(Float, default=30.0)
    stand_in_box = Column(String, default="Middle")

    # Situational and game/at-bat progression
    runners_on_base_modifier = Column(Float, default=0.0)
    game_progression_fatigue_rate = Column(Float, default=0.01)
    at_bat_progression_decay = Column(Float, default=0.008)

    # Sprint and baserunning parameters
    sprint_speed = Column(Float, default=27.0)  # ft/sec
    steal_aggression = Column(Float, default=0.5)

    # Catcher pop time & framing
    pop_time = Column(Float, default=2.0)  # seconds
    framing_rating = Column(Float, default=0.5)

    # Defensive range rating
    outs_above_average = Column(Integer, default=0)

    # Bullpen / Pitcher attributes
    pitcher_type = Column(String, default="Reliever")  # "Starter", "Reliever", "Closer"
    pitcher_arm_angle = Column(String, default="Three-Quarters")
    pitcher_rubber_position = Column(String, default="Middle")
    pitcher_velocity = Column(Float, default=93.0)
    pitcher_command = Column(Float, default=0.5)
    pitcher_movement = Column(Float, default=0.5)
    pitcher_windup_efficiency = Column(Float, default=0.8)
    pitcher_pitch_selection = Column(String, default="Fastball:0.6,Slider:0.2,Curveball:0.1,Changeup:0.1")
    stamina_pct = Column(Float, default=1.0)

    team = relationship("Team", back_populates="players")


class SystemState(Base):
    __tablename__ = "system_state"

    key = Column(String, primary_key=True, default="active_team_context")
    active_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
