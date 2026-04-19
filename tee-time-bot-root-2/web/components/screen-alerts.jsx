"use client";
import { Icon } from "@/components/primitives";
import { ALERTS } from "@/lib/data";

const cream='#F4EFE4', forest='#0E2A1F';

const kindStyle = k => ({
  snipe:   { accent:'var(--signal-green)', glyph:'zap' },
  new:     { accent:'var(--brass-500)', glyph:'sparkle' },
  deal:    { accent:'var(--signal-amber)', glyph:'dollar' },
  rare:    { accent:'var(--signal-red)', glyph:'flag' },
  digest:  { accent:'var(--forest-600)', glyph:'clock' },
}[k]);

export default function ScreenAlerts() {
  return (
    <div style={{ background: cream, minHeight:'100%', fontFamily:'var(--f-ui)', paddingBottom: 120 }}>
      <div style={{ paddingTop: 58, padding:'58px 20px 10px', display:'flex', alignItems:'center' }}>
        <div className="eyebrow">Signals</div>
        <div style={{ flex: 1 }}/>
        <div className="tnum" style={{ fontSize:11, color:'var(--forest-600)' }}>3 unread</div>
      </div>

      <div style={{ padding:'6px 20px 20px' }}>
        <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic',
          fontSize: 40, lineHeight: 1, letterSpacing:-1, color: forest }}>
          High-value pings, only.
        </div>
        <div style={{ fontSize: 12, color:'var(--forest-600)', marginTop: 10 }}>
          You&apos;ll hear from us when it actually matters. No feed slop.
        </div>
      </div>

      <div style={{ padding:'0 20px 16px', display:'flex', gap: 6, overflow:'auto' }} className="noscroll">
        {['All','Snipes','Prime','Deals','Rare'].map((l,i)=>(
          <button key={l} style={{
            height: 30, padding:'0 12px', borderRadius: 999,
            background: i===0 ? forest : 'transparent',
            color: i===0 ? cream : forest,
            border: i===0 ? 'none' : '1px solid var(--hair-strong)',
            fontSize: 12, fontWeight: 500, whiteSpace:'nowrap',
          }}>{l}</button>
        ))}
      </div>

      <div style={{ padding:'0 20px' }}>
        {ALERTS.map((a,i)=>{
          const st = kindStyle(a.kind);
          const unread = i < 3;
          return (
            <div key={a.id} style={{
              position:'relative',
              padding: '16px 4px 16px 20px',
              borderBottom: i<ALERTS.length-1 ? '1px solid var(--hair)' : 'none',
              display:'grid', gridTemplateColumns:'auto 1fr auto', gap: 12,
            }}>
              {unread && <span style={{ position:'absolute', left: 0, top: 24, width: 5, height: 5, borderRadius:'50%', background: st.accent }}/>}
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: a.state==='success' ? forest : 'rgba(14,42,31,0.05)',
                border: a.state==='success' ? 'none' : `1px solid ${st.accent}`,
                display:'flex', alignItems:'center', justifyContent:'center',
              }}>
                <Icon name={st.glyph} size={16}
                  color={a.state==='success' ? 'var(--brass-400)' : st.accent}/>
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ display:'flex', alignItems:'center', gap: 8, marginBottom: 2 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: forest }}>{a.title}</span>
                  {a.state==='success' && <Icon name="check" size={13} color="var(--signal-green)"/>}
                </div>
                <div style={{ fontSize: 12, color:'var(--forest-600)', marginBottom: 4 }}>
                  <span style={{ color: forest }}>{a.course}</span> · {a.time}
                </div>
                <div style={{ fontSize: 12, color:'var(--forest-600)', lineHeight: 1.45 }}>
                  {a.body}
                </div>
              </div>
              <div className="tnum" style={{ fontSize: 10, color:'var(--forest-300)', letterSpacing: 0.3 }}>
                {a.age}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
