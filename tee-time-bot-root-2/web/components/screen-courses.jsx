"use client";
import { TierChip, Sparkline, Icon } from "@/components/primitives";
import { COURSES } from "@/lib/data";

const cream='#F4EFE4', forest='#0E2A1F';

export default function ScreenCourses() {
  return (
    <div style={{ background: cream, minHeight:'100%', fontFamily:'var(--f-ui)', paddingBottom: 120 }}>
      <div style={{ paddingTop: 58, padding:'58px 20px 6px' }}>
        <div className="eyebrow">Courses</div>
        <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic',
          fontSize: 40, lineHeight: 1, letterSpacing:-1, color: forest, marginTop: 6 }}>
          The watchlist.
        </div>
        <div style={{ fontSize: 12, color:'var(--forest-600)', marginTop: 10 }}>
          40 Chicago-area courses. Pin the ones you care about.
        </div>
      </div>

      <div style={{ padding:'18px 20px 12px' }}>
        <div style={{
          height: 44, borderRadius: 14,
          background:'#fff', border:'1px solid var(--hair)',
          display:'flex', alignItems:'center', padding:'0 14px', gap: 10,
        }}>
          <Icon name="search" size={16} color="var(--forest-600)"/>
          <span style={{ fontSize: 13, color:'var(--forest-600)' }}>Search course, city, or designer…</span>
        </div>
      </div>

      <div style={{ padding:'0 20px 12px', display:'flex', gap: 6, overflow:'auto' }} className="noscroll">
        {['All 40','★ Pinned (7)','A+ only','Within 30mi','Designer'].map((l,i)=>(
          <button key={l} style={{
            height: 30, padding:'0 12px', borderRadius: 999,
            background: i===1 ? forest : 'transparent',
            color: i===1 ? cream : forest,
            border: i===1 ? 'none' : '1px solid var(--hair-strong)',
            fontSize: 12, whiteSpace:'nowrap',
          }}>{l}</button>
        ))}
      </div>

      <div style={{ padding:'0 20px' }}>
        {COURSES.map((c,i) => (
          <div key={c.id} style={{
            padding:'14px 4px',
            display:'grid', gridTemplateColumns:'auto 1fr auto', gap: 12,
            alignItems:'center',
            borderBottom: i<COURSES.length-1 ? '1px solid var(--hair)' : 'none',
          }}>
            <div className="tnum" style={{
              width: 22, fontSize: 11, color:'var(--forest-300)',
              fontFamily:'var(--f-mono)', letterSpacing: 0.4,
            }}>{String(i+1).padStart(2,'0')}</div>
            <div>
              <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom: 2 }}>
                <TierChip tier={c.tier}/>
                <div style={{ fontSize: 15, fontWeight: 500, color: forest }}>{c.name}</div>
              </div>
              <div style={{ fontSize: 11, color:'var(--forest-600)' }}>
                {c.city} · {c.distance}mi {c.dir} · <span className="tnum">{[3,5,2,8,4,1,6,2][i%8]}</span> open slots this week
              </div>
            </div>
            <Sparkline points={[3,5,2,6,4,7,3,5,6,4].map(v=>v+i)} width={56} height={18}/>
          </div>
        ))}
      </div>
    </div>
  );
}
