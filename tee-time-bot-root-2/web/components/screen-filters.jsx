"use client";
import React from "react";
import { Icon } from "@/components/primitives";

const cream = '#F4EFE4', forest = '#0E2A1F';

export default function ScreenFilters() {
  const [day, setDay] = React.useState('SAT');
  const [window_, setWindow] = React.useState([330, 480]);
  const [price, setPrice] = React.useState(130);
  const [players, setPlayers] = React.useState(2);
  const fmt = m => `${String(Math.floor(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`;

  return (
    <div style={{ background: cream, minHeight: '100%', fontFamily:'var(--f-ui)', paddingBottom: 120, position:'relative' }}>
      <div style={{ paddingTop: 58, padding:'58px 20px 14px', display:'flex', alignItems:'center' }}>
        <a href="/" style={{ background:'transparent', border:'none', padding:0, color:forest }}>
          <Icon name="close" size={22} color={forest}/>
        </a>
        <div style={{ flex:1 }}/>
        <div className="eyebrow">Filter</div>
        <div style={{ flex:1 }}/>
        <button style={{ background:'transparent', border:'none', padding:0,
          fontFamily:'var(--f-ui)', fontSize: 13, color:'var(--forest-600)' }}>Reset</button>
      </div>

      <div style={{ padding:'8px 20px' }}>
        <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic', fontSize:38, lineHeight:1,
          letterSpacing:-1, color:forest, marginBottom: 6 }}>
          Shape<br/>your weekend.
        </div>
        <div style={{ fontSize:13, color:'var(--forest-600)', marginTop: 10 }}>
          Fairway watches 40 courses. Tell it what counts.
        </div>
      </div>

      <div style={{ padding:'26px 20px 0' }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>Day</div>
        <div style={{ display:'flex', gap: 6 }}>
          {['SUN','MON','TUE','WED','THU','FRI','SAT'].map(d => (
            <button key={d} onClick={()=>setDay(d)} style={{
              flex: 1, height: 54, borderRadius: 12,
              background: d===day ? forest : 'transparent',
              color: d===day ? cream : forest,
              border: d===day ? 'none' : '1px solid var(--hair-strong)',
              fontFamily:'var(--f-mono)', fontSize: 11, letterSpacing: 0.4, fontWeight: 500,
              display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:2,
            }}>
              <span style={{ opacity: d===day ? 0.6 : 0.5 }}>{d}</span>
              <span className="tnum" style={{ fontSize: 16, letterSpacing:-0.3 }}>
                {['19','20','21','22','23','24','25'][['SUN','MON','TUE','WED','THU','FRI','SAT'].indexOf(d)]}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding:'26px 20px 0' }}>
        <div style={{ display:'flex', alignItems:'baseline', justifyContent:'space-between', marginBottom: 10 }}>
          <div className="eyebrow">Time window</div>
          <div className="tnum" style={{ fontFamily:'var(--f-mono)', fontSize:12, color:forest }}>
            {fmt(window_[0])} — {fmt(window_[1])}
          </div>
        </div>
        <div style={{ position:'relative', height: 60, background:'rgba(14,42,31,0.04)',
          border:'1px solid var(--hair)', borderRadius: 14, padding: 12 }}>
          <div style={{ position:'relative', height: '100%' }}>
            <div style={{ position:'absolute', top:'50%', left:0, right:0, height:1, background:'var(--hair-strong)' }}/>
            <div style={{ position:'absolute', top:'50%', height: 2,
              left: `${(window_[0]-300)/540*100}%`, right: `${(1 - (window_[1]-300)/540)*100}%`,
              background: 'var(--brass-500)' }}/>
            <div style={{ position:'absolute', top:0, bottom:0, left: `${(372-300)/540*100}%`, width:1,
              background:'var(--brass-500)', opacity: 0.5 }}/>
            <div style={{ position:'absolute', top:-2, left: `${(372-300)/540*100}%`,
              transform:'translateX(-50%)', fontFamily:'var(--f-mono)', fontSize:8, color:'var(--brass-500)',
              letterSpacing:0.4 }}>SR</div>
            {[window_[0], window_[1]].map((v,i)=>(
              <div key={i} style={{ position:'absolute', top:'50%', transform:'translate(-50%,-50%)',
                left: `${(v-300)/540*100}%`, width: 14, height: 28, borderRadius: 4,
                background: forest, boxShadow:'0 2px 4px rgba(0,0,0,0.2)' }}/>
            ))}
            <div style={{ position:'absolute', bottom:-4, left:0, fontFamily:'var(--f-mono)', fontSize:9, color:'var(--forest-600)' }}>5am</div>
            <div style={{ position:'absolute', bottom:-4, right:0, fontFamily:'var(--f-mono)', fontSize:9, color:'var(--forest-600)' }}>2pm</div>
          </div>
        </div>
      </div>

      <div style={{ padding:'26px 20px 0' }}>
        <div style={{ display:'flex', alignItems:'baseline', justifyContent:'space-between', marginBottom: 10 }}>
          <div className="eyebrow">Max price</div>
          <div className="tnum" style={{ fontSize:13, color:forest }}>under ${price}</div>
        </div>
        <div style={{ display:'flex', gap:6 }}>
          {[60,80,100,130,160,200].map(p => (
            <button key={p} onClick={()=>setPrice(p)} style={{
              flex:1, height: 42, borderRadius: 10,
              background: p===price ? forest : 'transparent',
              color: p===price ? cream : 'var(--forest-700)',
              border: p===price ? 'none' : '1px solid var(--hair)',
              fontFamily:'var(--f-mono)', fontSize:12, fontWeight:500,
            }}>${p}</button>
          ))}
        </div>
      </div>

      <div style={{ padding:'26px 20px 0' }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>Players</div>
        <div style={{ display:'flex', gap:8 }}>
          {[1,2,3,4].map(n => (
            <button key={n} onClick={()=>setPlayers(n)} style={{
              flex:1, height: 52, borderRadius: 12,
              background: n===players ? forest : 'transparent',
              color: n===players ? cream : 'var(--forest-700)',
              border: n===players ? 'none' : '1px solid var(--hair-strong)',
              fontFamily:'var(--f-display)', fontStyle:'italic', fontSize:22,
            }}>{n}</button>
          ))}
        </div>
      </div>

      <div style={{ padding:'26px 20px 0' }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>Must-play courses</div>
        <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
          {['Cog Hill #4','Cantigny','Mistwood','Harborside','Seven Bridges','Thunderhawk','Glen Club'].map((c,i) => (
            <button key={c} style={{
              height: 32, padding:'0 12px', borderRadius: 999,
              background: i<3 ? forest : 'transparent',
              color: i<3 ? cream : forest,
              border: i<3 ? 'none' : '1px solid var(--hair-strong)',
              fontSize: 12, fontWeight: 500, display:'flex', alignItems:'center', gap:6,
            }}>
              {i<3 && <Icon name="check" size={12} color={cream}/>}
              {c}
            </button>
          ))}
          <button style={{
            height: 32, padding:'0 12px', borderRadius: 999,
            background:'transparent', border:'1px dashed var(--hair-strong)',
            color:'var(--forest-600)', fontSize: 12,
            display:'flex', alignItems:'center', gap:4,
          }}>
            <Icon name="plus" size={12} color="var(--forest-600)"/>
            Add course
          </button>
        </div>
      </div>

      <div style={{ position:'absolute', left: 20, right: 20, bottom: 24, zIndex: 10 }}>
        <button style={{
          width:'100%', height: 54, borderRadius: 16,
          background: forest, color: cream, border:'none',
          fontFamily:'var(--f-ui)', fontSize: 15, fontWeight: 600, letterSpacing: 0.2,
          display:'flex', alignItems:'center', justifyContent:'center', gap: 10,
          boxShadow:'0 10px 30px -10px rgba(14,42,31,0.4)',
        }}>
          Show 12 matches
          <Icon name="arrow-up-right" size={14} color={cream}/>
        </button>
      </div>
    </div>
  );
}
