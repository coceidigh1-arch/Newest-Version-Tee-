"use client";
// Mobile "Today" dashboard — warm clubby tone, forest-on-cream with hero card in dark forest.

import {
  ScoreRing, TierChip, SignalBadge, SlotDots, WxIcon, SunriseLine,
  SectionLabel, Icon,
} from "@/components/primitives";
import { MarkFlag } from "@/components/brand";

const cream = '#F4EFE4';
const forest = '#0E2A1F';

export default function ScreenDashboard({ teeTimes = [], courses = [], isSample = true, totalCount }) {
  const courseById = Object.fromEntries(courses.map(c => [c.id, c]));
  const hero = teeTimes[0];
  const rest = teeTimes.slice(1, 5);
  const heroCourse = hero ? courseById[hero.course] : null;
  if (!hero || !heroCourse) {
    return (
      <div style={{ background: cream, minHeight: '100%', padding: '80px 24px', fontFamily:'var(--f-ui)', color: forest }}>
        <div style={{ fontFamily:'var(--f-display)', fontStyle:'italic', fontSize: 32, letterSpacing:-1 }}>
          No tee times yet.
        </div>
        <div style={{ fontSize: 13, color:'var(--forest-600)', marginTop: 10 }}>
          The scanner hasn&apos;t surfaced any open windows. Check back soon.
        </div>
      </div>
    );
  }
  const resultsLabel = totalCount ? `${totalCount} results · sort: score` : `${teeTimes.length} results · sort: score`;

  return (
    <div style={{ background: cream, minHeight: '100%', paddingBottom: 100, fontFamily:'var(--f-ui)' }}>
      <div style={{
        paddingTop: 58, padding:'58px 20px 8px',
        display:'flex', alignItems:'center', justifyContent:'space-between',
      }}>
        <MarkFlag size={34} color={forest} bg="transparent"/>
        <div style={{ display:'flex', alignItems:'center', gap: 12 }}>
          <button style={iconBtn()}>
            <Icon name="search" size={18} color={forest}/>
          </button>
          <div style={{
            width: 32, height:32, borderRadius:'50%',
            background:'var(--forest-800)',
            display:'flex', alignItems:'center', justifyContent:'center',
            color: cream, fontFamily:'var(--f-display)', fontStyle:'italic', fontSize:15,
          }}>M</div>
        </div>
      </div>

      <div style={{ padding:'12px 20px 18px' }}>
        <div className="eyebrow">Saturday · April 25</div>
        <div style={{
          fontFamily:'var(--f-display)', fontStyle:'italic',
          fontSize: 46, lineHeight: 1.0, color: forest,
          letterSpacing:-1.2, marginTop: 6,
        }}>
          Morning, Marcus.
        </div>
        <div style={{
          marginTop: 10, fontSize: 14, color:'var(--forest-600)',
          lineHeight: 1.45, maxWidth: 320,
        }}>
          We scanned <span className="tnum" style={{color:forest}}>{courses.length || 40} courses</span> overnight.
          {isSample ? " Sample data shown — " : " "}
          {teeTimes.length} window{teeTimes.length === 1 ? "" : "s"} fit you today.
        </div>
      </div>

      <div style={{
        margin:'0 20px 22px', padding:'10px 14px',
        background:'rgba(14,42,31,0.04)',
        border:'1px solid var(--hair)',
        borderRadius: 999,
        display:'flex', alignItems:'center', gap: 10,
        fontFamily:'var(--f-mono)', fontSize: 11, color:'var(--forest-700)',
      }}>
        <span style={{
          width: 8, height: 8, borderRadius:'50%',
          background: 'var(--signal-green)',
          animation:'pulse 1.6s ease-in-out infinite',
        }}/>
        <span style={{ letterSpacing: 0.4 }}>LIVE · scanning Cantigny · next sweep 00:47</span>
        <span style={{ flex:1 }}/>
        <Icon name="chev" size={12} color="var(--forest-600)"/>
      </div>

      <div style={{ padding: '0 20px 22px' }}>
        <HeroCard tt={hero} course={heroCourse}/>
      </div>

      <SectionLabel extra={resultsLabel}>Next best</SectionLabel>
      <div style={{ padding:'0 20px' }}>
        {rest.map(tt => (
          <TeeRow key={tt.id} tt={tt} course={courseById[tt.course]}/>
        ))}
      </div>

      <div style={{ padding:'18px 20px 30px' }}>
        <button style={{
          width:'100%', height: 48, borderRadius: 14,
          background:'transparent',
          border:'1px solid var(--hair-strong)',
          fontFamily:'var(--f-ui)', fontSize: 14, fontWeight:500,
          color: forest, letterSpacing: 0.2,
          display:'flex', alignItems:'center', justifyContent:'center', gap:8,
        }}>
          See all {totalCount || teeTimes.length} matches
          <Icon name="chev" size={14} color={forest}/>
        </button>
      </div>

      <TabBar active="home"/>
    </div>
  );
}

function iconBtn(){
  return {
    width: 32, height: 32, borderRadius: '50%',
    background:'transparent', border:'1px solid var(--hair-strong)',
    display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer',
    padding: 0,
  };
}

export function HeroCard({ tt, course }) {
  return (
    <div className="grain-dark" style={{
      position:'relative',
      background:'var(--forest-900)',
      color:'#F4EFE4',
      borderRadius: 22,
      padding: 22,
      overflow: 'hidden',
      boxShadow:'0 30px 60px -25px rgba(14,42,31,0.55), 0 1px 0 rgba(244,239,228,0.06) inset',
    }}>
      <svg width="180" height="180" viewBox="0 0 180 180" style={{
        position:'absolute', right:-50, top:-50, opacity:0.18, pointerEvents:'none'
      }}>
        <g stroke="#F4EFE4" fill="none" strokeWidth="0.6">
          <circle cx="90" cy="90" r="80"/>
          <circle cx="90" cy="90" r="60"/>
          <circle cx="90" cy="90" r="40"/>
          <circle cx="90" cy="90" r="20"/>
        </g>
        <circle cx="90" cy="90" r="2" fill="var(--brass-500)"/>
      </svg>

      <div style={{ display:'flex', alignItems:'center', gap: 8, marginBottom: 14 }}>
        <span className="eyebrow on-dark">#1 · Best fit today</span>
        <span style={{ flex: 1 }}/>
        <SignalBadge kind="prime" dark/>
        {tt.signals.includes('rare') && <SignalBadge kind="rare" dark/>}
      </div>

      <div style={{
        fontFamily:'var(--f-display)', fontStyle:'italic',
        fontSize: 38, lineHeight: 1.0, letterSpacing: -1,
        marginBottom: 4,
      }}>
        {course.name}
      </div>
      <div style={{ fontSize: 12, color:'var(--sand-400)', letterSpacing:0.1, marginBottom: 20 }}>
        {course.short} · {course.city} · {course.distance} mi {course.dir}
      </div>

      <div style={{
        display:'grid',
        gridTemplateColumns: '1fr auto',
        gap: 16, alignItems:'end',
        marginBottom: 18,
      }}>
        <div>
          <div style={{ display:'flex', alignItems:'baseline', gap:10 }}>
            <div style={{
              fontFamily:'var(--f-mono)', fontSize: 44, lineHeight: 1,
              color:'#F4EFE4', letterSpacing: -1.5, fontWeight: 500,
            }}>{tt.time}</div>
            <div style={{
              fontFamily:'var(--f-ui)', fontSize: 14, color:'var(--sand-400)',
              letterSpacing: 0.2,
            }}>{tt.day}</div>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap: 8, marginTop: 8 }}>
            <WxIcon kind={tt.wx} size={14} color="var(--sand-400)"/>
            <span className="tnum" style={{ fontSize: 11, color:'var(--sand-400)' }}>
              {tt.temp}° · {tt.wind}mph
            </span>
            <span style={{ width:1, height:10, background:'rgba(244,239,228,0.15)' }}/>
            <SunriseLine sunrise={tt.sunrise} time={tt.time} width={80} dark/>
          </div>
        </div>

        <ScoreRing value={tt.score} size={60} stroke={2} dark/>
      </div>

      <div style={{
        fontSize: 13, lineHeight: 1.5,
        color: 'rgba(244,239,228,0.75)',
        paddingTop: 14,
        borderTop: '1px solid rgba(244,239,228,0.10)',
        marginBottom: 16,
      }}>
        {tt.reason}
      </div>

      <div style={{ display:'flex', gap: 10 }}>
        <button style={{
          flex: 1, height: 50, borderRadius: 14,
          background: 'var(--brass-500)',
          color:'var(--ink-900)',
          border:'none',
          fontFamily:'var(--f-ui)', fontSize: 15, fontWeight: 600,
          letterSpacing: 0.2,
          display:'flex', alignItems:'center', justifyContent:'center', gap: 8,
        }}>
          Book · <span className="tnum">${tt.price}</span>
          <Icon name="arrow-up-right" size={14} color="var(--ink-900)"/>
        </button>
        <button style={{
          height: 50, width: 50, borderRadius: 14,
          background:'transparent', border:'1px solid rgba(244,239,228,0.22)',
          color:'#F4EFE4',
          display:'flex', alignItems:'center', justifyContent:'center',
        }}>
          <Icon name="zap" size={18} color="var(--brass-400)"/>
        </button>
      </div>

      <div style={{
        display:'flex', alignItems:'center', gap: 14,
        marginTop: 16, fontSize: 11, fontFamily:'var(--f-mono)',
        color:'var(--sand-400)', letterSpacing: 0.3,
      }}>
        <TierChip tier={course.tier} dark/>
        <span style={{ display:'flex', alignItems:'center', gap:5 }}>
          <Icon name="users" size={11} color="var(--sand-400)"/>
          <span>{tt.players}·UP</span>
        </span>
        <span style={{ display:'flex', alignItems:'center', gap:5 }}>
          <SlotDots total={4} taken={4 - tt.slotsLeft} dark/>
          <span>{tt.slotsLeft}/4</span>
        </span>
        <span style={{ marginLeft:'auto' }}>via {course.platform}</span>
      </div>
    </div>
  );
}

export function TeeRow({ tt, course }) {
  return (
    <div style={{
      display:'grid',
      gridTemplateColumns: '52px 1fr auto',
      gap: 14, alignItems:'center',
      padding: '16px 4px',
      borderBottom: '1px solid var(--hair)',
    }}>
      <div>
        <div className="tnum" style={{
          fontSize: 20, fontWeight: 500, color: 'var(--ink-900)',
          lineHeight: 1, letterSpacing: -0.6,
        }}>{tt.time}</div>
        <div style={{
          fontFamily:'var(--f-mono)', fontSize: 10, color:'var(--forest-600)',
          marginTop: 4, letterSpacing: 0.4,
        }}>{tt.day}</div>
      </div>

      <div style={{ minWidth: 0 }}>
        <div style={{ display:'flex', alignItems:'center', gap: 6, marginBottom: 3 }}>
          <TierChip tier={course.tier}/>
          <div style={{
            fontSize: 15, fontWeight: 500, color:'var(--ink-900)',
            letterSpacing: -0.1, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap',
          }}>{course.name}</div>
        </div>
        <div style={{
          display:'flex', alignItems:'center', gap: 10,
          fontSize: 11, color:'var(--forest-600)',
        }}>
          <span style={{ display:'flex', alignItems:'center', gap:4 }}>
            <WxIcon kind={tt.wx} size={11} color="var(--forest-600)"/>
            <span className="tnum">{tt.temp}°</span>
          </span>
          <span>{course.distance}mi {course.dir}</span>
          <span className="tnum">${tt.price}</span>
          {tt.signals[0] && <SignalBadge kind={tt.signals[0]}/>}
        </div>
      </div>

      <div style={{ display:'flex', alignItems:'center', gap: 8 }}>
        <ScoreRing value={tt.score} size={36} stroke={2}/>
      </div>
    </div>
  );
}

export function TabBar({ active = 'home' }) {
  const items = [
    { key:'home',   icon:'home',    label:'Today',  href:'/' },
    { key:'search', icon:'search',  label:'Browse', href:'/filters' },
    { key:'map',    icon:'map',     label:'Map',    href:'/courses' },
    { key:'snipe',  icon:'zap',     label:'Snipes', href:'/snipes' },
    { key:'bell',   icon:'bell',    label:'Alerts', href:'/alerts' },
  ];
  return (
    <div style={{
      position:'absolute', left: 12, right: 12, bottom: 12,
      background:'rgba(14,42,31,0.92)',
      backdropFilter:'blur(16px) saturate(180%)',
      WebkitBackdropFilter:'blur(16px) saturate(180%)',
      borderRadius: 24, padding: '10px 8px',
      display:'flex',
      boxShadow:'0 16px 32px -10px rgba(14,42,31,0.45), inset 0 1px 0 rgba(244,239,228,0.08)',
      zIndex: 20,
    }}>
      {items.map(it => {
        const on = it.key === active;
        return (
          <a key={it.key} href={it.href} style={{
            flex:1, display:'flex', flexDirection:'column', alignItems:'center',
            gap: 4, padding: '6px 0',
            textDecoration:'none',
            color: on ? 'var(--brass-400)' : 'rgba(244,239,228,0.55)',
          }}>
            <Icon name={it.icon} size={18} color="currentColor"/>
            <span style={{
              fontFamily:'var(--f-ui)', fontSize: 9, fontWeight: on ? 600 : 500,
              letterSpacing: 0.4, textTransform:'uppercase',
            }}>{it.label}</span>
          </a>
        );
      })}
    </div>
  );
}
