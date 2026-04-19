"use client";
// Shared building blocks

export function ScoreRing({ value = 92, size = 44, stroke = 3, dark = false, accent = 'var(--brass-500)' }) {
  const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;
  const off = C * (1 - value/100);
  const ring = dark ? 'rgba(244,239,228,0.18)' : 'rgba(14,42,31,0.12)';
  const txt = dark ? '#F4EFE4' : '#0E2A1F';
  return (
    <div style={{ position:'relative', width:size, height:size }}>
      <svg width={size} height={size} style={{ transform:'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} stroke={ring} strokeWidth={stroke} fill="none"/>
        <circle cx={size/2} cy={size/2} r={r} stroke={accent} strokeWidth={stroke}
          fill="none" strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={off}/>
      </svg>
      <div style={{
        position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center',
        fontFamily:'var(--f-mono)', fontSize: size*0.32, fontWeight: 600, color: txt,
        letterSpacing:-0.5,
      }}>{value}</div>
    </div>
  );
}

export function TierChip({ tier = 'A+', dark = false }) {
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', justifyContent:'center',
      minWidth: 30, height: 20, padding:'0 6px',
      borderRadius: 4,
      fontFamily:'var(--f-mono)', fontSize:11, fontWeight:600,
      letterSpacing:0.2,
      color: dark ? '#F4EFE4' : '#0E2A1F',
      border:`1px solid ${dark ? 'rgba(244,239,228,0.25)' : 'rgba(14,42,31,0.20)'}`,
      background: dark ? 'rgba(244,239,228,0.05)' : 'transparent',
    }}>{tier}</span>
  );
}

export function SignalBadge({ kind = 'rare', dark = false }) {
  const MAP = {
    rare:   { label:'RARE',     color:'var(--signal-red)' },
    hot:    { label:'HOT',      color:'var(--signal-red)' },
    deal:   { label:'DEAL',     color:'var(--signal-amber)' },
    best:   { label:'BEST FIT', color:'var(--brass-500)' },
    prime:  { label:'PRIME',    color:'var(--brass-500)' },
    new:    { label:'NEW',      color:'var(--signal-green)' },
    locked: { label:'SNIPING',  color:'var(--signal-green)' },
  };
  const m = MAP[kind] || MAP.best;
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', gap:5,
      height: 18, padding:'0 7px',
      borderRadius: 3,
      fontFamily:'var(--f-ui)', fontSize:10, fontWeight:600, letterSpacing:0.12,
      color: m.color, background:'transparent',
      border:`1px solid ${m.color}`,
      textTransform:'uppercase',
    }}>
      <span style={{
        width:4, height:4, borderRadius:'50%', background:m.color,
        boxShadow:`0 0 6px ${m.color}`,
      }}/>
      {m.label}
    </span>
  );
}

export function SlotDots({ total = 4, taken = 0, dark = false }) {
  const on = dark ? '#F4EFE4' : '#0E2A1F';
  const off = dark ? 'rgba(244,239,228,0.18)' : 'rgba(14,42,31,0.15)';
  return (
    <div style={{ display:'flex', gap:3, alignItems:'center' }}>
      {Array.from({length: total}).map((_,i)=>(
        <span key={i} style={{
          width:6, height:6, borderRadius:'50%',
          background: i < (total - taken) ? on : off,
        }}/>
      ))}
    </div>
  );
}

export function Sparkline({ points = [4,3,5,2,6,7,4,8,5,6], width=80, height=22, color = 'var(--forest-700)' }) {
  const max = Math.max(...points), min = Math.min(...points);
  const dx = width / (points.length - 1);
  const norm = v => height - 2 - ((v-min)/(max-min||1)) * (height-4);
  const d = points.map((v,i)=>`${i===0?'M':'L'}${(i*dx).toFixed(1)},${norm(v).toFixed(1)}`).join(' ');
  return (
    <svg width={width} height={height} style={{ display:'block' }}>
      <path d={d} fill="none" stroke={color} strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function WxIcon({ kind = 'sun', size = 14, color = 'currentColor' }) {
  if (kind === 'sun') return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.4" strokeLinecap="round">
      <circle cx="12" cy="12" r="4"/>
      {[0,45,90,135,180,225,270,315].map(a=>{
        const r = a*Math.PI/180;
        return <line key={a} x1={12+Math.cos(r)*7.5} y1={12+Math.sin(r)*7.5} x2={12+Math.cos(r)*10.5} y2={12+Math.sin(r)*10.5}/>;
      })}
    </svg>
  );
  if (kind === 'cloud') return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 18h11a4 4 0 000-8 6 6 0 00-11.7-1A3.5 3.5 0 007 18z"/>
    </svg>
  );
  if (kind === 'wind') return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.4" strokeLinecap="round">
      <path d="M3 8h12a3 3 0 100-6M3 14h16a3 3 0 110 6M3 11h9"/>
    </svg>
  );
  if (kind === 'drizzle') return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 14h11a4 4 0 000-8 6 6 0 00-11.7-1A3.5 3.5 0 007 14z"/>
      <path d="M9 18l-1 2M13 18l-1 2M17 18l-1 2"/>
    </svg>
  );
  return null;
}

export function SunriseLine({ sunrise = '06:12', time = '06:42', width = 120, dark = false }) {
  const toT = s => { const [h,m]=s.split(':').map(Number); return ((h*60+m)-300)/540; };
  const sr = Math.max(0, Math.min(1, toT(sunrise)));
  const t  = Math.max(0, Math.min(1, toT(time)));
  const line = dark ? 'rgba(244,239,228,0.25)' : 'rgba(14,42,31,0.2)';
  return (
    <div style={{ width, height: 18, position:'relative' }}>
      <div style={{ position:'absolute', left:0, right:0, top: 9, height: 1, background: line }}/>
      <div style={{ position:'absolute', left: `${sr*100}%`, top:3, width: 1, height: 12, background: 'var(--brass-500)' }}/>
      <div style={{ position:'absolute', left: `calc(${sr*100}% + 4px)`, top:0, fontSize:8,
        fontFamily:'var(--f-mono)', color:'var(--brass-500)', letterSpacing:0.3 }}>SR</div>
      <div style={{ position:'absolute', left: `calc(${t*100}% - 4px)`, top: 4,
        width: 8, height: 8, borderRadius:'50%',
        background: dark ? '#F4EFE4' : '#0E2A1F' }}/>
    </div>
  );
}

export function SectionLabel({ children, extra, dark = false }) {
  return (
    <div style={{
      display:'flex', alignItems:'baseline', justifyContent:'space-between',
      padding: '0 20px', marginBottom: 10,
    }}>
      <div className="eyebrow" style={{ color: dark ? 'var(--sand-400)' : 'var(--forest-600)' }}>{children}</div>
      {extra && <div style={{
        fontFamily:'var(--f-mono)', fontSize:11,
        color: dark ? 'rgba(244,239,228,0.6)' : 'rgba(14,42,31,0.55)',
      }}>{extra}</div>}
    </div>
  );
}

export function Icon({ name, size = 16, color = 'currentColor', strokeWidth = 1.5 }) {
  const p = { width:size, height:size, viewBox:'0 0 24 24', fill:'none',
    stroke: color, strokeWidth, strokeLinecap:'round', strokeLinejoin:'round' };
  switch(name) {
    case 'bell': return (<svg {...p}><path d="M6 8a6 6 0 1112 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 004 0"/></svg>);
    case 'search': return (<svg {...p}><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>);
    case 'filter': return (<svg {...p}><path d="M3 5h18M6 12h12M10 19h4"/></svg>);
    case 'map': return (<svg {...p}><path d="M9 3L3 6v15l6-3 6 3 6-3V3l-6 3-6-3z"/><path d="M9 3v15M15 6v15"/></svg>);
    case 'flag': return (<svg {...p}><path d="M4 21V4"/><path d="M4 4h12l-2 4 2 4H4"/></svg>);
    case 'clock': return (<svg {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>);
    case 'chev': return (<svg {...p}><path d="M9 6l6 6-6 6"/></svg>);
    case 'close': return (<svg {...p}><path d="M6 6l12 12M18 6L6 18"/></svg>);
    case 'plus': return (<svg {...p}><path d="M12 5v14M5 12h14"/></svg>);
    case 'dollar': return (<svg {...p}><path d="M12 3v18M17 7H9.5a2.5 2.5 0 000 5H14a2.5 2.5 0 010 5H7"/></svg>);
    case 'users': return (<svg {...p}><circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0114 0"/><path d="M16 4a4 4 0 010 8M22 21a7 7 0 00-5-6.7"/></svg>);
    case 'home': return (<svg {...p}><path d="M3 11l9-7 9 7v9a2 2 0 01-2 2h-4v-7h-6v7H5a2 2 0 01-2-2z"/></svg>);
    case 'zap': return (<svg {...p}><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/></svg>);
    case 'sparkle': return (<svg {...p}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/></svg>);
    case 'arrow-up-right': return (<svg {...p}><path d="M7 17L17 7M9 7h8v8"/></svg>);
    case 'check': return (<svg {...p}><path d="M4 12l5 5L20 6"/></svg>);
    case 'pin': return (<svg {...p}><path d="M12 22s7-7.5 7-13a7 7 0 10-14 0c0 5.5 7 13 7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>);
    default: return null;
  }
}
