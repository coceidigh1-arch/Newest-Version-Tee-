"use client";
import { ScoreRing, TierChip, SignalBadge, WxIcon, Icon } from "@/components/primitives";

const cream = '#F4EFE4', forest = '#0E2A1F';

export default function ScreenDetail({ teeTime, teeTimes, courses = [] }) {
  // Accept either a single teeTime or legacy array.
  const tt = teeTime || (teeTimes && teeTimes[0]);
  const course = tt ? courses.find(c => c.id === tt.course) : null;
  if (!tt || !course) {
    return (
      <div style={{ background: cream, minHeight: '100%', padding: '80px 24px', fontFamily:'var(--f-ui)', color: forest }}>
        <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic', fontSize: 28 }}>No tee time selected.</div>
      </div>
    );
  }
  return (
    <div style={{ background: cream, minHeight:'100%', fontFamily:'var(--f-ui)', paddingBottom: 120, position:'relative' }}>
      <div style={{ paddingTop: 58, padding:'58px 20px 8px', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
        <a href="/" style={{ background:'transparent', border:'none', padding:0, transform:'rotate(180deg)', color:forest }}>
          <Icon name="chev" size={20} color={forest}/>
        </a>
        <div className="eyebrow">Tee time · #{String(tt.id).slice(0, 8).toUpperCase()}</div>
        <Icon name="pin" size={18} color={forest}/>
      </div>

      <div style={{
        margin:'12px 20px 20px', height: 160, borderRadius: 16,
        position:'relative', overflow:'hidden',
        background:'linear-gradient(135deg, var(--forest-800), var(--forest-700))',
      }}>
        <svg width="100%" height="100%" viewBox="0 0 400 160" preserveAspectRatio="none" style={{ position:'absolute', inset:0 }}>
          <path d="M0,110 Q 100,70 200,95 T 400,80 L 400,160 L 0,160 Z" fill="var(--forest-900)" opacity="0.6"/>
          <path d="M0,130 Q 120,100 240,120 T 400,110 L 400,160 L 0,160 Z" fill="var(--ink-900)" opacity="0.8"/>
          <circle cx="340" cy="40" r="18" fill="var(--brass-500)" opacity="0.8"/>
        </svg>
        <div style={{ position:'absolute', bottom:14, left:16, right:16,
          display:'flex', alignItems:'flex-end', justifyContent:'space-between', color: cream }}>
          <div>
            <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic', fontSize: 26, lineHeight: 1, letterSpacing:-0.6 }}>
              {course.name}
            </div>
            <div style={{ fontSize: 11, opacity: 0.8, marginTop: 4, fontFamily:'var(--f-mono)', letterSpacing:0.4 }}>
              EST. 1964 · RICK JACOBSON · PAR 72
            </div>
          </div>
          <TierChip tier={course.tier} dark/>
        </div>
      </div>

      <div style={{ padding:'0 20px 6px', display:'grid', gridTemplateColumns:'1fr auto', gap: 10, alignItems:'center' }}>
        <div>
          <div className="eyebrow">{tt.humanDate || tt.day}</div>
          <div style={{ fontFamily:'var(--f-mono)', fontSize: 56, lineHeight: 1, color: forest, letterSpacing:-2, marginTop: 8 }}>
            {tt.time}
          </div>
        </div>
        <ScoreRing value={tt.score} size={76} stroke={3}/>
      </div>

      <div style={{ padding:'10px 20px 0', display:'flex', gap: 6, flexWrap:'wrap' }}>
        {(tt.signals || []).map(s => <SignalBadge key={s} kind={s}/>)}
      </div>

      <div style={{ padding:'22px 20px 0' }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>Why it scored {tt.score}</div>
        <div style={{ background:'#fff', borderRadius: 14, border:'1px solid var(--hair)', overflow:'hidden' }}>
          {[
            ['Course priority', '#1 must-play', 30, 30],
            ['Day fit', 'Saturday · preferred', 20, 20],
            ['Time window', '6:42 — prime center', 18, 20],
            ['Price', '$98 · $22 under max', 13, 15],
            ['Weather', 'Sunny · 6mph wind', 15, 15],
          ].map(([l,v,s,max],i) => (
            <div key={i} style={{
              display:'grid', gridTemplateColumns:'110px 1fr 40px',
              gap: 12, alignItems:'center',
              padding: '12px 16px',
              borderBottom: i<4 ? '1px solid var(--hair)' : 'none',
            }}>
              <div style={{ fontSize: 13, color: forest, fontWeight: 500 }}>{l}</div>
              <div style={{ fontSize: 12, color:'var(--forest-600)' }}>{v}</div>
              <div className="tnum" style={{ fontSize: 12, textAlign:'right', color: forest, fontWeight: 600 }}>
                +{s}<span style={{ color:'var(--forest-300)', fontWeight:400 }}>/{max}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding:'22px 20px 0' }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>Conditions at tee off</div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap: 8 }}>
          {[
            { icon: tt.wx || 'sun', label: 'Temp', value: tt.temp != null ? `${tt.temp}°` : '—' },
            { icon: 'wind', label: 'Wind', value: tt.wind != null ? `${tt.wind} mph` : '—' },
            { icon: 'drizzle', label: 'Precip', value: tt.precip != null ? `${tt.precip}%` : '—' },
          ].map((s,i)=>(
            <div key={i} style={{
              background:'#fff', border:'1px solid var(--hair)', borderRadius: 12,
              padding: 12,
            }}>
              <WxIcon kind={s.icon} size={16} color="var(--forest-700)"/>
              <div style={{ fontSize: 10, color:'var(--forest-600)', marginTop: 8, letterSpacing: 0.3, textTransform:'uppercase' }}>{s.label}</div>
              <div className="tnum" style={{ fontSize: 15, fontWeight: 500, color: forest, marginTop: 2 }}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ position:'absolute', left: 20, right: 20, bottom: 24, zIndex: 10,
        display:'flex', gap: 10 }}>
        <a
          href={tt.booking_url || "#"}
          target={tt.booking_url ? "_blank" : undefined}
          rel={tt.booking_url ? "noopener noreferrer" : undefined}
          style={{
            flex: 1, height: 54, borderRadius: 16,
            background: forest, color: cream, border:'none',
            fontFamily:'var(--f-ui)', fontSize: 15, fontWeight: 600,
            display:'flex', alignItems:'center', justifyContent:'center', gap: 8,
            boxShadow:'0 10px 30px -10px rgba(14,42,31,0.4)',
            textDecoration:'none',
            opacity: tt.booking_url ? 1 : 0.5,
            pointerEvents: tt.booking_url ? 'auto' : 'none',
          }}
        >
          Book on {course.platform}
          {tt.price > 0 && <> · <span className="tnum">${tt.price}</span></>}
          <Icon name="arrow-up-right" size={16} color={cream}/>
        </a>
      </div>
    </div>
  );
}
