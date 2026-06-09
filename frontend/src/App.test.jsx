import { render, screen, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import React from 'react';
import App from './App';

// Mock global fetch to decouple from active backend service
vi.stubGlobal('fetch', vi.fn().mockImplementation((url) => {
  if (url.includes('/api/v1/config')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        active_team_id: 112,
        active_team_name: "Chicago Cubs",
        location_abbr: "CHC",
        stadium_name: "Wrigley Field",
        elevation: 600.0,
        base_park_factor: 1.03,
        managerial_override: {
          fatigue_threshold: 5,
          clutch_weight: 1.2,
          defensive_sub_inning: 7,
          cold_bench_friction_tax: 0.10
        },
        environmental_context: {
          game_id: "2026_CHC_GAME_01",
          temperature: 72.0,
          humidity: 45.0,
          wind_velocity: 14.0,
          wind_direction: "Out"
        },
        roster_size: 13
      })
    });
  }
  
  if (url.includes('/api/v1/players')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve([])
    });
  }

  if (url.includes('/api/v1/optimize/lineup')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        optimal_lineup: [],
        optimized_metric: 0.0,
        base_vs_optimized_ops_delta: 0.0
      })
    });
  }

  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve({})
  });
}));

test('renders dashboard with active team scope selector', async () => {
  render(<App />);
  
  // Wait for fetch mocks to resolve and render components
  await waitFor(() => {
    expect(screen.getByText(/Active Team Scope:/i)).toBeInTheDocument();
  });
  
  expect(screen.getByText(/Chicago Cubs/i)).toBeInTheDocument();
});
