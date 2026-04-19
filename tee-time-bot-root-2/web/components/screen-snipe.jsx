"use client";
import React from "react";
import { SectionLabel, Icon } from "@/components/primitives";
import { getChatId, setChatId } from "@/lib/tg";
import { listSnipes, createSnipe } from "@/lib/snipes-client";
import { listCourses } from "@/lib/alerts-client";

const cream = '#F4EFE4', forest = '#0E2A1F';
const stateMap = {
  armed:    { label: 'ARMED',    color: 'var(--brass-500)' },
  scanning: { label: 'SCANNING', color: 'var(--signal-green)' },
  booked:   { label: 'BOOKED',   color: 'var(--forest-700)' },
  pending:  { label: 'PENDING',  color: 'var(--brass-500)' },
  active:   { label: 'ACTIVE',   color: 'var(--brass-500)' },
};

export default function ScreenSnipe() {
  const [chatId, setChatIdLocal] = React.useState("");
  const [hydrated, setHydrated] = React.useState(false);
  const [snipes, setSnipes] = React.useState(null);
  const [courses, setCourses] = React.useState([]);
  const [creating, setCreating] = React.useState(false);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    const existing = getChatId();
    setChatIdLocal(existing);
    setHydrated(true);
  }, []);

  React.useEffect(() => {
    if (!chatId) { setSnipes([]); return; }
    (async () => {
      try {
        const [s, c] = await Promise.all([listSnipes(chatId), listCourses()]);
        setSnipes(s);
        setCourses(c);
      } catch (e) {
        setErr(e.message);
        setSnipes([]);
      }
    })();
  }, [chatId]);

  async function refresh() {
    try { setSnipes(await listSnipes(chatId)); } catch (e) { setErr(e.message); }
  }

  async function handleCreate(body) {
    setErr("");
    try { await createSnipe(chatId, body); setCreating(false); refresh(); }
    catch (e) { setErr(e.message); }
  }

  function handleDisconnect() {
    setChatId("");
    setChatIdLocal("");
    setSnipes(null);
  }

  return (
    <div style={{ background: cream, minHeight: '100%', fontFamily: 'var(--f-ui)', paddingBottom: 120 }}>
      <div style={{ paddingTop: 58, padding: '58px 20px 6px' }}>
        <div className="eyebrow">Snipes</div>
        <div style={{
          fontFamily: 'var(--f-display)', fontStyle: 'italic',
          fontSize: 40, lineHeight: 1, letterSpacing: -1, color: forest, marginTop: 6,
        }}>
          Set it.<br/>We&apos;ll beat the refresh.
        </div>
      </div>

      {!hydrated && <div style={dim}>…</div>}

      {hydrated && !chatId && (
        <ConnectForm onConnect={(id) => { setChatId(id); setChatIdLocal(id); }}/>
      )}

      {hydrated && chatId && (
        <>
          <div style={{ padding: '18px 20px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="mono" style={{ fontSize: 11, color: 'var(--forest-600)' }}>
              Chat #{chatId}
            </span>
            <span style={{ flex: 1 }}/>
            <button onClick={handleDisconnect} style={btnGhost}>
              Disconnect
            </button>
          </div>

          {!creating && (
            <div style={{ padding: '16px 20px 4px' }}>
              <button onClick={() => setCreating(true)} style={btnPrimary}>
                <Icon name="plus" size={16} color={cream}/>
                New snipe
              </button>
            </div>
          )}

          {creating && (
            <div style={{ padding: '12px 20px' }}>
              <SnipeForm
                courses={courses}
                onCancel={() => setCreating(false)}
                onSubmit={handleCreate}
              />
            </div>
          )}

          {err && <div style={{ ...errStyle, margin: '0 20px' }}>{err}</div>}

          <SectionLabel extra={<span className="tnum">{snipes?.length ?? 0} active</span>}>Queue</SectionLabel>

          {snipes === null && <div style={{ padding: '20px', ...dim }}>Loading…</div>}

          {snipes && snipes.length === 0 && (
            <div style={{ padding: '10px 20px', ...dim }}>
              No snipes yet. Tap <strong style={{ color: forest }}>New snipe</strong> to create one,
              or create one from the Telegram bot with <span className="mono" style={{ color: forest }}>/snipe</span>.
            </div>
          )}

          <div style={{ padding: '0 20px' }}>
            {(snipes || []).map(s => <SnipeRow key={s.id} s={s}/>)}
          </div>
        </>
      )}
    </div>
  );
}

function ConnectForm({ onConnect }) {
  const [v, setV] = React.useState("");
  return (
    <div style={{ padding: '20px 20px 0' }}>
      <div style={{
        background: '#fff', border: '1px solid var(--hair)', borderRadius: 14,
        padding: 16,
      }}>
        <div style={{ fontSize: 14, color: forest, marginBottom: 8, fontWeight: 500 }}>
          Connect the bot
        </div>
        <div style={{ fontSize: 12, color: 'var(--forest-600)', lineHeight: 1.5, marginBottom: 12 }}>
          Open Telegram, message <span className="mono" style={{ color: forest }}>@TeeTimeBot</span>,
          and send <span className="mono" style={{ color: forest }}>/whoami</span>. It&apos;ll reply
          with your chat id. Paste it below.
        </div>
        <input
          value={v}
          onChange={e => setV(e.target.value.replace(/[^0-9]/g, ""))}
          placeholder="e.g. 892451011"
          inputMode="numeric"
          style={input}
        />
        <button
          onClick={() => v && onConnect(v)}
          disabled={!v}
          style={{ ...btnPrimary, marginTop: 10, opacity: v ? 1 : 0.5, cursor: v ? 'pointer' : 'not-allowed' }}
        >
          Connect
        </button>
      </div>
    </div>
  );
}

function SnipeRow({ s }) {
  const st = stateMap[String(s.state || s.status || "pending").toLowerCase()] || stateMap.active;
  const isBooked = String(s.state || s.status || "").toLowerCase() === "booked";
  const isScanning = String(s.state || s.status || "").toLowerCase() === "scanning";
  const courseName = s.course_name || s.course_id || s.course || "Course";
  return (
    <div style={{
      background: isBooked ? forest : '#fff',
      color: isBooked ? cream : forest,
      borderRadius: 16,
      border: isBooked ? 'none' : '1px solid var(--hair)',
      padding: 16, marginBottom: 10,
      position: 'relative', overflow: 'hidden',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          fontFamily: 'var(--f-mono)', fontSize: 10, fontWeight: 600,
          letterSpacing: 0.4, color: isBooked ? 'var(--brass-400)' : st.color,
        }}>
          {isScanning && <span style={{
            width: 6, height: 6, borderRadius: '50%', background: st.color,
            animation: 'pulse 1.4s ease-in-out infinite',
          }}/>}
          {isBooked && <Icon name="check" size={11} color="var(--brass-400)"/>}
          {st.label}
        </span>
        <span style={{ flex: 1 }}/>
        <span className="tnum" style={{
          fontSize: 11, color: isBooked ? 'var(--sand-400)' : 'var(--forest-600)',
        }}>{s.fires_at || s.created_at || ""}</span>
      </div>
      <div style={{
        fontFamily: 'var(--f-display)', fontStyle: 'italic',
        fontSize: 24, lineHeight: 1, letterSpacing: -0.5, marginBottom: 8,
      }}>
        {courseName}
      </div>
      <div style={{
        display: 'flex', gap: 14, alignItems: 'center',
        fontSize: 12, color: isBooked ? 'var(--sand-400)' : 'var(--forest-600)',
        marginBottom: 14,
      }}>
        <span>{s.date_from || s.date}</span>
        {s.earliest_time && s.latest_time && (
          <span className="tnum">{s.earliest_time}–{s.latest_time}</span>
        )}
        <span className="tnum">{(s.players || s.min_players || 0)}·UP</span>
        {(s.max_price != null) && <span className="tnum">≤${s.max_price}</span>}
      </div>
      {isBooked && (
        <div style={{
          borderTop: '1px solid rgba(244,239,228,0.12)', paddingTop: 10,
          fontSize: 11, color: 'var(--sand-400)',
        }}>
          Booked — check Telegram for the confirmation link.
        </div>
      )}
    </div>
  );
}

function SnipeForm({ courses, onCancel, onSubmit }) {
  const today = new Date().toISOString().slice(0, 10);
  const plus7 = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
  const [courseId, setCourseId] = React.useState(courses[0]?.id || "");
  const [dateFrom, setDateFrom] = React.useState(today);
  const [dateTo, setDateTo] = React.useState(plus7);
  const [earliest, setEarliest] = React.useState("05:30");
  const [latest, setLatest] = React.useState("09:00");
  const [players, setPlayers] = React.useState(2);
  const [maxPrice, setMaxPrice] = React.useState(130);

  React.useEffect(() => {
    if (!courseId && courses[0]) setCourseId(courses[0].id);
  }, [courses, courseId]);

  function submit() {
    if (!courseId) return;
    onSubmit({
      course_id: courseId,
      date_from: dateFrom,
      date_to: dateTo,
      earliest_time: earliest,
      latest_time: latest,
      players: Number(players),
      max_price: Number(maxPrice),
    });
  }

  return (
    <div style={{
      background: '#fff', border: '1px solid var(--hair)', borderRadius: 14, padding: 14,
    }}>
      <Field label="Course">
        <select value={courseId} onChange={e => setCourseId(e.target.value)} style={input}>
          {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </Field>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <Field label="From date">
          <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} style={input}/>
        </Field>
        <Field label="To date">
          <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} style={input}/>
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <Field label="Earliest">
          <input type="time" value={earliest} onChange={e => setEarliest(e.target.value)} style={input}/>
        </Field>
        <Field label="Latest">
          <input type="time" value={latest} onChange={e => setLatest(e.target.value)} style={input}/>
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <Field label="Players">
          <div style={{ display: 'flex', gap: 4 }}>
            {[1, 2, 3, 4].map(n => (
              <button key={n} onClick={() => setPlayers(n)} type="button" style={{
                flex: 1, height: 34, borderRadius: 8,
                background: n === players ? forest : 'transparent',
                color: n === players ? cream : forest,
                border: n === players ? 'none' : '1px solid var(--hair)',
                fontSize: 13, fontFamily: 'var(--f-mono)', cursor: 'pointer',
              }}>{n}</button>
            ))}
          </div>
        </Field>
        <Field label="Max price">
          <input type="number" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} style={input}/>
        </Field>
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <button onClick={submit} style={btnPrimary}>Create snipe</button>
        <button onClick={onCancel} style={btnGhost}>Cancel</button>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label style={{ display: 'block', marginBottom: 10 }}>
      <div className="eyebrow" style={{ marginBottom: 4 }}>{label}</div>
      {children}
    </label>
  );
}

const input = {
  width: '100%', height: 36, padding: '0 10px', borderRadius: 8,
  border: '1px solid var(--hair-strong)', background: 'var(--cream-50)',
  fontFamily: 'var(--f-ui)', fontSize: 13, color: forest, boxSizing: 'border-box',
};
const btnPrimary = {
  width: '100%', height: 52, borderRadius: 14,
  background: forest, color: cream, border: 'none',
  fontFamily: 'var(--f-ui)', fontSize: 14, fontWeight: 600,
  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
  cursor: 'pointer',
};
const btnGhost = {
  background: 'transparent', border: '1px solid var(--hair-strong)',
  padding: '6px 12px', borderRadius: 8, fontSize: 12, color: forest,
  cursor: 'pointer',
};
const dim = { fontSize: 13, color: 'var(--forest-600)', padding: '10px 0' };
const errStyle = {
  fontSize: 12, color: 'var(--signal-red)', padding: '8px 10px',
  background: 'rgba(248,113,113,0.08)', borderRadius: 8, marginBottom: 10,
};
