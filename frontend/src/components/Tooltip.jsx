import React, { useState } from 'react';

export default function Tooltip({ text, children }) {
    const [show, setShow] = useState(false);
    return (
        <div 
            className="tooltip-container" 
            onMouseEnter={() => setShow(true)} 
            onMouseLeave={() => setShow(false)}
            style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}
        >
            {children}
            <div className="tooltip-icon" style={{ 
                marginLeft: '6px', 
                background: 'rgba(255,255,255,0.1)', 
                color: 'var(--text-muted)', 
                borderRadius: '50%', 
                width: '14px', 
                height: '14px', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                fontSize: '10px', 
                cursor: 'help' 
            }}>?</div>
            {show && (
                <div className="tooltip-box">
                    {text}
                </div>
            )}
        </div>
    );
}
