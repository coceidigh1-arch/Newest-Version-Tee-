"use client";
import {
  ScoreRing, TierChip, SignalBadge, SlotDots, WxIcon, Icon,
} from "@/components/primitives";
import { MarkFlag } from "@/components/brand";

const cream='#F4EFE4', forest='#0E2A1F';

export default function ScreenDesktop({ teeTimes = [], courses = [] }) {
  const COURSES = courses;
  const TEE_TIMES = teeTimes;
  return (
    <div style={{
      width: 1440, height: 900, background: cream,
      fontFamily:'var(--f-ui)', color: forest,
      display:'grid',
      gridTemplateColumns:'240px 1fr 380px',
      gridTemplateRows:'60px 1fr',
      overflow:'hidden',
    }}>
      <div style={{
        gridColumn:'1 / -1',
        display:'flex', alignItems:'center', padding:'0 24px',
        borderBottom:'1px solid var(--hair)',
        background: cream,
      }}>
        <MarkFlag size={26} color={forest} bg="transparent"/>
        <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic', fontSize: 22, letterSpacing:-0.5, marginLeft: 8 }}>
          Fairway<span style={{ color:'var(--brass-500)' }}>.</span>
        </div>
        <div style={{ width: 1, height: 20, background:'var(--hair-strong)', margin:'0 22px' }}/>

        <div style={{
          flex:1, maxWidth: 520, height: 36, borderRadius: 10,
          border:'1px solid var(--hair)', background:'rgba(255,255,255,0.5)',
          display:'flex', alignItems:'center', padding:'0 12px', gap: 10,
        }}>
          <Icon name="search" size={14} color="var(--forest-600)"/>
          <span style={{ fontSize: 13, color:'var(--forest-600)' }}>
            Try &quot;sat before 9am under $90&quot; or /cog
          </span>
          <span style={{ flex:1 }}/>
          <span className="mono" style={{
            fontSize: 10, padding:'2px 5px', borderRadius: 3,
            background:'var(--cream-200)', color:'var(--forest-600)', letterSpacing: 0.3,
          }}>⌘ K</span>
        </div>

        <div style={{ flex:1 }}/>

        <div style={{ display:'flex', alignItems:'center', gap: 10,
          fontFamily:'var(--f-mono)', fontSize: 11, color:'var(--forest-700)' }}>
          <span style={{ width: 6, height: 6, borderRadius:'50%', background:'var(--signal-green)', boxShadow:'0 0 6px var(--signal-green)' }}/>
          <span>LIVE · 00:47 to next sweep</span>
        </div>

        <div style={{ width: 1, height: 20, background:'var(--hair-strong)', margin:'0 16px' }}/>

        <button style={{
          height: 32, padding:'0 14px', borderRadius: 8,
          background: forest, color: cream, border:'none',
          fontSize: 12, fontWeight: 600, display:'flex', alignItems:'center', gap: 6,
        }}>
          <Icon name="zap" size={13} color="var(--brass-400)"/>
          New snipe
        </button>

        <div style={{
          marginLeft: 12, width: 28, height: 28, borderRadius:'50%',
          background:'var(--forest-800)', color: cream,
          display:'flex', alignItems:'center', justifyContent:'center',
          fontFamily:'var(--f-display)', fontStyle:'italic', fontSize: 13,
        }}>M</div>
      </div>

      <div style={{ borderRight:'1px solid var(--hair)', padding:'18px 18px 24px', overflow:'auto' }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>View</div>
        {[
          ['Today',      '12', true],
          ['This weekend', '34'],
          ['Must-plays',  '8'],
          ['Deals',       '15'],
          ['Rare windows','3'],
          ['Sniping',     '4'],
        ].map(([l, n, on]) => (
          <div key={l} style={{
            display:'flex', alignItems:'center', padding:'6px 8px', borderRadius: 6,
            background: on ? 'rgba(14,42,31,0.06)' : 'transparent',
            fontSize: 13, color: forest, fontWeight: on ? 600 : 400,
            marginBottom: 2, cursor:'pointer',
          }}>
            <span>{l}</span>
            <span style={{ flex:1 }}/>
            <span className="tnum" style={{ fontSize: 11, color:'var(--forest-600)' }}>{n}</span>
          </div>
        ))}

        <div style={{ marginTop: 22 }}>
          <div className="eyebrow" style={{ marginBottom: 10 }}>Day</div>
          <div style={{ display:'flex', gap:4 }}>
            {['S','M','T','W','T','F','S'].map((d,i)=>(
              <div key={i} style={{
                flex:1, height: 36, borderRadius: 6,
                display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
                background: (i===0 || i===6) ? forest : 'transparent',
                color: (i===0 || i===6) ? cream : forest,
                border: (i===0 || i===6) ? 'none' : '1px solid var(--hair)',
                fontSize: 10, fontFamily:'var(--f-mono)',
              }}>
                <span style={{ opacity: 0.6 }}>{d}</span>
                <span className="tnum" style={{ fontSize: 11 }}>{19+i}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 22 }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom: 8 }}>
            <div className="eyebrow">Time</div>
            <div className="tnum" style={{ fontSize: 11, color:'var(--forest-600)' }}>5:30 — 8:00</div>
          </div>
          <div style={{ height: 6, borderRadius: 3, background:'rgba(14,42,31,0.08)', position:'relative' }}>
            <div style={{ position:'absolute', left:'6%', right:'47%', top:0, bottom:0, background:'var(--brass-500)', borderRadius: 3 }}/>
          </div>
        </div>

        <div style={{ marginTop: 22 }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom: 8 }}>
            <div className="eyebrow">Max price</div>
            <div className="tnum" style={{ fontSize: 11, color:'var(--forest-600)' }}>$130</div>
          </div>
          <div style={{ height: 6, borderRadius: 3, background:'rgba(14,42,31,0.08)', position:'relative' }}>
            <div style={{ position:'absolute', left:0, width:'62%', top:0, bottom:0, background: forest, borderRadius: 3 }}/>
          </div>
        </div>

        <div style={{ marginTop: 22 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Players</div>
          <div style={{ display:'flex', gap: 4 }}>
            {[1,2,3,4].map(n => (
              <div key={n} style={{
                flex:1, height: 28, borderRadius: 6,
                background: n===2 ? forest : 'transparent',
                color: n===2 ? cream : forest,
                border: n===2 ? 'none' : '1px solid var(--hair)',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize: 12, fontFamily:'var(--f-mono)',
              }}>{n}</div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 22 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Must-play (8)</div>
          <div style={{ display:'flex', flexDirection:'column', gap: 4 }}>
            {['Cog Hill #4','Cantigny','Mistwood','Harborside','Seven Bridges'].map(c => (
              <div key={c} style={{
                padding:'5px 8px', borderRadius: 5, fontSize: 12,
                color: forest, background:'rgba(14,42,31,0.04)',
                display:'flex', alignItems:'center', gap: 6,
              }}>
                <span style={{ width: 5, height: 5, borderRadius:'50%', background:'var(--brass-500)' }}/>
                {c}
              </div>
            ))}
            <div style={{ fontSize: 11, color:'var(--forest-600)', padding:'4px 8px' }}>+ 3 more</div>
          </div>
        </div>
      </div>

      <div style={{ overflow:'auto', padding:'20px 24px' }}>
        <div style={{ display:'flex', alignItems:'flex-end', justifyContent:'space-between', marginBottom: 18 }}>
          <div>
            <div className="eyebrow" style={{ marginBottom: 4 }}>Saturday · April 25</div>
            <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic',
              fontSize: 40, lineHeight: 1, letterSpacing:-1, color: forest }}>
              {TEE_TIMES.length} prime windows
            </div>
          </div>
          <div style={{ display:'flex', gap: 6 }}>
            {['Sort: Score','View: Table','Export'].map(l=>(
              <button key={l} style={{
                height: 30, padding:'0 12px', borderRadius: 6,
                background:'transparent', border:'1px solid var(--hair)',
                fontSize: 12, color: forest, fontFamily:'var(--f-ui)',
                display:'flex', alignItems:'center', gap: 6,
              }}>{l} <Icon name="chev" size={10} color="var(--forest-600)"/></button>
            ))}
          </div>
        </div>

        <div style={{
          display:'grid',
          gridTemplateColumns: '40px 90px 1fr 80px 90px 80px 120px 70px 100px',
          gap: 12, alignItems:'center',
          padding:'8px 12px',
          borderBottom:'1px solid var(--hair)',
          fontFamily:'var(--f-mono)', fontSize: 10, letterSpacing: 0.5,
          color:'var(--forest-600)', textTransform:'uppercase',
        }}>
          <span>RK</span>
          <span>TIME</span>
          <span>COURSE</span>
          <span style={{ textAlign:'right' }}>PRICE</span>
          <span>WX</span>
          <span>SLOTS</span>
          <span>SIGNALS</span>
          <span style={{ textAlign:'right' }}>SCORE</span>
          <span style={{ textAlign:'right' }}>ACTION</span>
        </div>

        {TEE_TIMES.map((tt,i) => {
          const course = COURSES.find(c=>c.id===tt.course);
          const isTop = i===0;
          return (
            <a key={tt.id} href={`/detail/${tt.id}`} style={{
              display:'grid',
              gridTemplateColumns: '40px 90px 1fr 80px 90px 80px 120px 70px 100px',
              gap: 12, alignItems:'center',
              padding:'14px 12px',
              borderBottom:'1px solid var(--hair)',
              background: isTop ? 'rgba(184,147,90,0.08)' : 'transparent',
              borderLeft: isTop ? '2px solid var(--brass-500)' : '2px solid transparent',
              textDecoration:'none', color:'inherit',
            }}>
              <span className="tnum" style={{ fontSize: 13, color:'var(--forest-600)', fontWeight: 500 }}>
                {String(i+1).padStart(2,'0')}
              </span>
              <div>
                <div className="tnum" style={{ fontSize: 17, fontWeight: 500, letterSpacing:-0.3 }}>{tt.time}</div>
                <div style={{ fontFamily:'var(--f-mono)', fontSize: 9, color:'var(--forest-600)', letterSpacing: 0.3 }}>
                  {tt.day} · {tt.date.slice(5)}
                </div>
              </div>
              <div style={{ display:'flex', alignItems:'center', gap: 8 }}>
                <TierChip tier={course.tier}/>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500 }}>{course.name}</div>
                  <div style={{ fontSize: 10, color:'var(--forest-600)', marginTop: 2 }}>
                    {course.city} · {course.distance}mi {course.dir} · {course.platform}
                  </div>
                </div>
              </div>
              <div className="tnum" style={{ fontSize: 14, textAlign:'right', fontWeight: 500 }}>
                ${tt.price}
              </div>
              <div style={{ display:'flex', alignItems:'center', gap: 6, fontSize: 11 }}>
                <WxIcon kind={tt.wx} size={13} color="var(--forest-700)"/>
                <span className="tnum">{tt.temp != null ? `${tt.temp}°` : "—"}</span>
                <span className="tnum" style={{ color:'var(--forest-600)' }}>{tt.wind != null ? `${tt.wind}mph` : ""}</span>
              </div>
              <div style={{ display:'flex', alignItems:'center', gap: 6 }}>
                <SlotDots total={4} taken={4-tt.slotsLeft}/>
                <span className="tnum" style={{ fontSize: 11, color:'var(--forest-600)' }}>{tt.slotsLeft}/4</span>
              </div>
              <div style={{ display:'flex', gap: 4, flexWrap:'wrap' }}>
                {tt.signals.map(s => <SignalBadge key={s} kind={s}/>)}
              </div>
              <div style={{ display:'flex', justifyContent:'flex-end' }}>
                <ScoreRing value={tt.score} size={34} stroke={2}/>
              </div>
              <div style={{ display:'flex', justifyContent:'flex-end', gap: 6 }}>
                <span
                  onClick={(e) => {
                    if (tt.booking_url) {
                      e.preventDefault();
                      e.stopPropagation();
                      window.open(tt.booking_url, '_blank', 'noopener,noreferrer');
                    }
                  }}
                  style={{
                    height: 30, padding:'0 12px', borderRadius: 6,
                    background: isTop ? 'var(--brass-500)' : forest,
                    color: isTop ? 'var(--ink-900)' : cream,
                    border:'none', fontSize: 12, fontWeight: 600,
                    display:'inline-flex', alignItems:'center', gap: 4,
                    cursor: tt.booking_url ? 'pointer' : 'not-allowed',
                    opacity: tt.booking_url ? 1 : 0.5,
                  }}
                >
                  Book <Icon name="arrow-up-right" size={11} color={isTop ? 'var(--ink-900)' : cream}/>
                </span>
              </div>
            </a>
          );
        })}
      </div>

      <div style={{ borderLeft:'1px solid var(--hair)', display:'flex', flexDirection:'column' }}>
        <div style={{
          height: 340, background:'var(--forest-900)', color: cream,
          position:'relative', overflow:'hidden',
        }}>
          <svg width="100%" height="100%" viewBox="0 0 380 340" style={{ position:'absolute', inset:0 }}>
            <path d="M320,0 Q 260,60 280,180 T 300,340 L 380,340 L 380,0 Z" fill="var(--ink-900)" opacity="0.6"/>
            <g stroke="rgba(244,239,228,0.08)" strokeWidth="1" fill="none">
              <path d="M0,170 L 320,170"/>
              <path d="M150,0 L 150,340"/>
              <path d="M0,260 Q 120,240 200,270 T 330,260"/>
              <path d="M50,0 Q 80,120 40,240 T 70,340"/>
            </g>
            <circle cx="290" cy="170" r="4" fill="var(--sand-400)"/>
            <text x="298" y="172" fill="var(--sand-400)" fontFamily="var(--f-mono)" fontSize="9" letterSpacing="0.5">CHICAGO</text>
            {[
              { x: 110, y: 230, tier:'A+', score: 96, hot: true, label:'Cog #4' },
              { x: 180, y: 180, tier:'A+', score: 93, hot: true, label:'Cantigny' },
              { x: 90,  y: 250, tier:'A+', score: 91 },
              { x: 260, y: 190, tier:'A+', score: 84, label:'Harborside' },
              { x: 140, y: 200, tier:'A+', score: 79 },
              { x: 220, y: 40,  tier:'A+', score: 66 },
              { x: 90,  y: 90,  tier:'A' },
              { x: 170, y: 290, tier:'A' },
              { x: 40,  y: 280, tier:'A' },
              { x: 60,  y: 150, tier:'A' },
              { x: 210, y: 130, tier:'A' },
              { x: 250, y: 270, tier:'A' },
              { x: 70,  y: 30,  tier:'B+' },
            ].map((p, i) => {
              const r = p.tier === 'A+' ? 5.5 : p.tier === 'A' ? 4 : 3;
              const fill = p.hot ? 'var(--brass-500)' : (p.score ? 'var(--sand-400)' : 'rgba(244,239,228,0.35)');
              return (
                <g key={i}>
                  {p.hot && (
                    <circle cx={p.x} cy={p.y} r={r+6} fill="none" stroke="var(--brass-500)" strokeWidth="0.5" opacity="0.6">
                      <animate attributeName="r" values={`${r+4};${r+10};${r+4}`} dur="2s" repeatCount="indefinite"/>
                      <animate attributeName="opacity" values="0.6;0;0.6" dur="2s" repeatCount="indefinite"/>
                    </circle>
                  )}
                  <circle cx={p.x} cy={p.y} r={r} fill={fill} opacity={p.score ? 1 : 0.5}/>
                  {p.label && <text x={p.x+8} y={p.y+3} fill="var(--cream-100)" fontFamily="var(--f-ui)" fontSize="9">{p.label}</text>}
                </g>
              );
            })}
          </svg>

          <div style={{
            position:'absolute', top: 14, left: 14, right: 14,
            display:'flex', alignItems:'center', justifyContent:'space-between',
          }}>
            <div className="eyebrow" style={{ color:'var(--sand-400)' }}>Coverage · {COURSES.length} courses</div>
            <div style={{
              display:'flex', alignItems:'center', gap: 6,
              fontFamily:'var(--f-mono)', fontSize: 9, color:'var(--sand-400)', letterSpacing: 0.3,
            }}>
              <span style={{ width: 4, height: 4, borderRadius:'50%', background:'var(--brass-500)' }}/>
              HOT
              <span style={{ width: 4, height: 4, borderRadius:'50%', background:'var(--sand-400)', marginLeft: 8 }}/>
              AVAIL
            </div>
          </div>
        </div>

        <div style={{ flex:1, overflow:'auto', padding: 20, background: cream }}>
          <div style={{ display:'flex', alignItems:'center', gap: 10, marginBottom: 14 }}>
            <span style={{
              width: 7, height: 7, borderRadius:'50%',
              background: 'var(--signal-green)',
              boxShadow:'0 0 8px var(--signal-green)',
              animation:'pulse 1.6s ease-in-out infinite',
            }}/>
            <div className="eyebrow">Live scan</div>
            <span style={{ flex:1 }}/>
            <span className="tnum" style={{ fontSize: 10, color:'var(--forest-600)' }}>next sweep 00:47</span>
          </div>

          <div style={{ display:'flex', flexDirection:'column', gap: 8 }}>
            {[
              { course:'Cantigny',         status:'scanning', meta:'Whoosh · 3 new slots' },
              { course:'Cog Hill #4',      status:'done',     meta:'ForeUp · 200ms' },
              { course:'Harborside Port',  status:'done',     meta:'GolfNow · 340ms' },
              { course:'Mistwood',         status:'done',     meta:'CPS · +$30 drop' },
              { course:'Seven Bridges',    status:'done',     meta:'GolfNow · 180ms' },
              { course:'The Glen Club',    status:'pending',  meta:'EZLinks · queued' },
              { course:'Thunderhawk',      status:'pending',  meta:'GolfNow · queued' },
            ].map((r,i)=>(
              <div key={i} style={{
                display:'grid', gridTemplateColumns:'14px 1fr auto', gap: 8, alignItems:'center',
                fontSize: 12,
              }}>
                <span style={{
                  width: 8, height: 8, borderRadius:'50%',
                  background: r.status==='scanning' ? 'var(--signal-green)' :
                              r.status==='done' ? 'var(--forest-600)' : 'var(--cream-300)',
                  boxShadow: r.status==='scanning' ? '0 0 6px var(--signal-green)' : 'none',
                }}/>
                <div>
                  <div style={{ fontWeight: r.status==='scanning' ? 600 : 400, color: forest }}>
                    {r.course}
                  </div>
                </div>
                <div className="tnum" style={{ fontSize: 10, color:'var(--forest-600)' }}>{r.meta}</div>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: 18, padding: 12, borderRadius: 10,
            background:'rgba(14,42,31,0.04)', border:'1px solid var(--hair)',
          }}>
            <div className="eyebrow" style={{ marginBottom: 8 }}>Today&apos;s stats</div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap: 10 }}>
              {[
                ['Courses', '40'],
                ['Sweeps', '186'],
                ['New slots', '+24'],
                ['Avg latency', '220ms'],
              ].map(([l,v]) => (
                <div key={l}>
                  <div style={{ fontSize: 10, color:'var(--forest-600)', letterSpacing:0.3, textTransform:'uppercase' }}>{l}</div>
                  <div className="tnum" style={{ fontSize: 18, fontWeight: 500, marginTop: 2 }}>{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
