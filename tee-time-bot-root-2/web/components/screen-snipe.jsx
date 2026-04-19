"use client";
import { SectionLabel, Icon } from "@/components/primitives";

const cream='#F4EFE4', forest='#0E2A1F';
const stateMap = {
  armed:    { label:'ARMED',     color:'var(--brass-500)' },
  scanning: { label:'SCANNING',  color:'var(--signal-green)' },
  booked:   { label:'BOOKED',    color:'var(--forest-700)' },
};

export default function ScreenSnipe({ snipes = [] }) {
  const SNIPES = snipes;
  return (
    <div style={{ background: cream, minHeight:'100%', fontFamily:'var(--f-ui)', paddingBottom: 120 }}>
      <div style={{ paddingTop: 58, padding:'58px 20px 6px' }}>
        <div className="eyebrow">Snipes</div>
        <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic',
          fontSize: 40, lineHeight: 1, letterSpacing:-1, color: forest, marginTop: 6 }}>
          Set it.<br/>We&apos;ll beat the refresh.
        </div>
      </div>

      <div style={{ padding:'24px 20px 8px' }}>
        <button style={{
          width:'100%', height: 52, borderRadius: 14,
          background: forest, color: cream, border:'none',
          fontFamily:'var(--f-ui)', fontSize: 14, fontWeight: 600,
          display:'flex', alignItems:'center', justifyContent:'center', gap: 8,
        }}>
          <Icon name="plus" size={16} color={cream}/>
          New snipe
        </button>
      </div>

      <SectionLabel extra={<span className="tnum">{SNIPES.length} active</span>}>Queue</SectionLabel>

      {SNIPES.length === 0 && (
        <div style={{ padding:'30px 20px', fontSize: 13, color:'var(--forest-600)', lineHeight: 1.55 }}>
          No snipes yet. Create one via the Telegram bot and it&apos;ll appear here.
          <div style={{ marginTop: 12, fontSize: 12, color:'var(--forest-300)' }}>
            Use <span className="mono" style={{ color: forest }}>/snipe</span> in the bot.
          </div>
        </div>
      )}

      <div style={{ padding:'0 20px' }}>
        {SNIPES.map(s => {
          const st = stateMap[s.state];
          const isBooked = s.state==='booked';
          const isScanning = s.state==='scanning';
          return (
            <div key={s.id} style={{
              background: isBooked ? forest : '#fff',
              color: isBooked ? cream : forest,
              borderRadius: 16,
              border: isBooked ? 'none' : '1px solid var(--hair)',
              padding: 16, marginBottom: 10,
              position:'relative', overflow:'hidden',
            }}>
              <div style={{ display:'flex', alignItems:'center', gap: 8, marginBottom: 10 }}>
                <span style={{
                  display:'inline-flex', alignItems:'center', gap: 6,
                  fontFamily:'var(--f-mono)', fontSize: 10, fontWeight: 600,
                  letterSpacing: 0.4, color: isBooked ? 'var(--brass-400)' : st.color,
                }}>
                  {isScanning && <span style={{
                    width: 6, height: 6, borderRadius:'50%', background: st.color,
                    animation:'pulse 1.4s ease-in-out infinite',
                  }}/>}
                  {isBooked && <Icon name="check" size={11} color="var(--brass-400)"/>}
                  {st.label}
                </span>
                <span style={{ flex:1 }}/>
                <span className="tnum" style={{
                  fontSize: 11, color: isBooked ? 'var(--sand-400)' : 'var(--forest-600)',
                }}>{s.fires}</span>
              </div>

              <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic',
                fontSize: 24, lineHeight: 1, letterSpacing:-0.5, marginBottom: 8 }}>
                {s.course}
              </div>

              <div style={{ display:'flex', gap: 14, alignItems:'center',
                fontSize: 12, color: isBooked ? 'var(--sand-400)' : 'var(--forest-600)',
                marginBottom: 14 }}>
                <span>{s.date}</span>
                <span className="tnum">{s.time}</span>
                <span className="tnum">{s.players}·UP</span>
                <span className="tnum">≤${s.maxPrice}</span>
              </div>

              {isScanning && (
                <div style={{ height: 4, borderRadius: 999, background:'rgba(14,42,31,0.06)', position:'relative', overflow:'hidden' }}>
                  <div style={{
                    position:'absolute', top:0, bottom:0, width:'40%',
                    background:'linear-gradient(90deg, transparent, var(--signal-green), transparent)',
                    animation:'sweep 2s ease-in-out infinite',
                  }}/>
                </div>
              )}

              {isBooked && (
                <div style={{
                  borderTop:'1px solid rgba(244,239,228,0.12)', paddingTop: 10,
                  fontSize: 11, color:'var(--sand-400)', display:'flex', justifyContent:'space-between',
                }}>
                  <span>Conf #MW-5521</span>
                  <span className="tnum">$125 · 4-up</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
