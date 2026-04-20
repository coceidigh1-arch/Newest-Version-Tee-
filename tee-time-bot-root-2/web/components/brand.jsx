"use client";
// Brand mark exploration for Fairway

export function MarkWordmark({ color = '#0E2A1F', size = 48 }) {
  return (
    <div style={{
      fontFamily: 'var(--f-display)',
      fontSize: size, lineHeight: 0.9,
      letterSpacing: -0.02 * size,
      fontStyle: 'italic',
      fontWeight: 400, color,
    }}>
      Fairway<span style={{ color: 'var(--brass-500)' }}>.</span>
    </div>
  );
}

export function MarkMonogram({ size = 72, color = '#0E2A1F', bg = '#F4EFE4' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 72 72">
      <rect width="72" height="72" rx="14" fill={bg}/>
      <path d="M36 10 L60 22 L60 50 L36 62 L12 50 L12 22 Z" fill="none" stroke={color} strokeWidth="1.3" opacity="0.25"/>
      <text x="36" y="48" textAnchor="middle"
        fontFamily="Instrument Serif, Georgia, serif"
        fontSize="40" fontStyle="italic" fill={color} fontWeight="400">F</text>
      <circle cx="54" cy="20" r="2.2" fill="var(--brass-500)"/>
    </svg>
  );
}

export function MarkFlag({ size = 72, color = '#0E2A1F', bg = '#F4EFE4' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 72 72">
      <rect width="72" height="72" rx="14" fill={bg}/>
      <line x1="28" y1="14" x2="28" y2="58" stroke={color} strokeWidth="1.6" strokeLinecap="round"/>
      <path d="M28 16 L52 22 L28 28 Z" fill={color}/>
      <line x1="18" y1="58" x2="54" y2="58" stroke={color} strokeWidth="1.6" strokeLinecap="round"/>
      <circle cx="38" cy="58" r="2.4" fill="var(--brass-500)"/>
    </svg>
  );
}

export function MarkLine({ size = 72, color = '#0E2A1F', bg = '#F4EFE4' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 72 72">
      <rect width="72" height="72" rx="14" fill={bg}/>
      <circle cx="36" cy="36" r="22" fill="none" stroke={color} strokeWidth="1"/>
      <circle cx="36" cy="36" r="14" fill="none" stroke={color} strokeWidth="1"/>
      <circle cx="36" cy="36" r="6" fill="none" stroke={color} strokeWidth="1"/>
      <circle cx="36" cy="36" r="1.6" fill="var(--brass-500)"/>
      <line x1="36" y1="8" x2="36" y2="16" stroke={color} strokeWidth="1" opacity="0.4"/>
      <line x1="36" y1="56" x2="36" y2="64" stroke={color} strokeWidth="1" opacity="0.4"/>
      <line x1="8"  y1="36" x2="16" y2="36" stroke={color} strokeWidth="1" opacity="0.4"/>
      <line x1="56" y1="36" x2="64" y2="36" stroke={color} strokeWidth="1" opacity="0.4"/>
    </svg>
  );
}

export function MarkHorizon({ size = 72, color = '#0E2A1F', bg = '#F4EFE4' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 72 72">
      <rect width="72" height="72" rx="14" fill={bg}/>
      <line x1="10" y1="44" x2="62" y2="44" stroke={color} strokeWidth="1.4"/>
      <circle cx="36" cy="44" r="14" fill="none" stroke={color} strokeWidth="1.4"/>
      <path d="M22 44 A14 14 0 0 1 50 44" fill={color}/>
      <path d="M48 50 L50 56 L46 56 Z" fill="var(--brass-500)"/>
    </svg>
  );
}

export function BrandLockup({ MarkC, bg, color, label }) {
  return (
    <div style={{
      background: bg, padding: '36px 32px', borderRadius: 2,
      display: 'flex', alignItems: 'center', gap: 16,
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    }}>
      <MarkC size={56} color={color} bg="transparent"/>
      <div>
        <div style={{
          fontFamily: 'var(--f-display)', fontStyle:'italic',
          fontSize: 40, lineHeight: 0.95, color,
          letterSpacing: -0.8,
        }}>Fairway<span style={{ color: 'var(--brass-500)' }}>.</span></div>
        <div className="eyebrow" style={{
          marginTop: 6, color: color === '#0E2A1F' ? 'var(--forest-600)' : 'var(--sand-400)',
        }}>{label}</div>
      </div>
    </div>
  );
}
