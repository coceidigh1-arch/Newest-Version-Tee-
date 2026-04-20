"use client";
import React from "react";
import { Icon } from "@/components/primitives";
import { getSessionId } from "@/lib/session";
import {
  listAlerts, createAlert, deleteAlert, listCourses,
} from "@/lib/alerts-client";

const cream = "#F4EFE4";
const forest = "#0E2A1F";

export default function WatchAlerts() {
  const [sessionId, setSessionId] = React.useState("");
  const [alerts, setAlerts] = React.useState(null); // null = loading
  const [courses, setCourses] = React.useState([]);
  const [creating, setCreating] = React.useState(false);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    const sid = getSessionId();
    setSessionId(sid);
    (async () => {
      try {
        const [a, c] = await Promise.all([listAlerts(sid), listCourses()]);
        setAlerts(a);
        setCourses(c);
      } catch (e) {
        setErr(e.message);
        setAlerts([]);
      }
    })();
  }, []);

  async function refresh() {
    try { setAlerts(await listAlerts(sessionId)); } catch (e) { setErr(e.message); }
  }

  async function handleCreate(data) {
    setErr("");
    try {
      await createAlert(sessionId, data);
      setCreating(false);
      refresh();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function handleDelete(id) {
    try { await deleteAlert(sessionId, id); refresh(); } catch (e) { setErr(e.message); }
  }

  return (
    <div style={{ padding: "14px 20px 8px" }}>
      <div style={{
        display: "flex", alignItems: "baseline", justifyContent: "space-between",
        marginBottom: 10,
      }}>
        <div className="eyebrow">Watch alerts</div>
        {!creating && (
          <button
            onClick={() => setCreating(true)}
            style={btnGhost}
          >
            <Icon name="plus" size={12} color={forest}/>
            New
          </button>
        )}
      </div>

      {err && <div style={errStyle}>{err}</div>}

      {creating && (
        <CreateForm
          courses={courses}
          onCancel={() => { setCreating(false); setErr(""); }}
          onSubmit={handleCreate}
        />
      )}

      {alerts === null ? (
        <div style={dim}>Loading your alerts…</div>
      ) : alerts.length === 0 ? (
        <div style={dim}>
          No watch alerts yet. Tap <strong style={{ color: forest }}>New</strong> to set one up —
          we&apos;ll email you when a matching window opens.
        </div>
      ) : (
        <div>
          {alerts.map(a => (
            <AlertRow key={a.id} a={a} onDelete={() => handleDelete(a.id)}/>
          ))}
        </div>
      )}
    </div>
  );
}

function AlertRow({ a, onDelete }) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "1fr auto",
      gap: 10, alignItems: "center",
      padding: "12px 0",
      borderBottom: "1px solid var(--hair)",
    }}>
      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: forest }}>
          {a.course_name || a.course_id}
        </div>
        <div style={{ fontSize: 11, color: "var(--forest-600)", marginTop: 2, fontFamily: "var(--f-mono)" }}>
          {a.earliest_time}–{a.latest_time} · {a.min_players}p
          {a.date_from && ` · ${a.date_from}`}
          {a.date_to && ` → ${a.date_to}`}
        </div>
      </div>
      <button
        onClick={onDelete}
        aria-label="Delete alert"
        style={{
          background: "transparent", border: "1px solid var(--hair-strong)",
          width: 28, height: 28, borderRadius: 8, cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}
      >
        <Icon name="close" size={12} color={forest}/>
      </button>
    </div>
  );
}

function CreateForm({ courses, onCancel, onSubmit }) {
  const [courseId, setCourseId] = React.useState(courses[0]?.id || "");
  const [earliest, setEarliest] = React.useState("05:30");
  const [latest, setLatest] = React.useState("09:00");
  const [players, setPlayers] = React.useState(2);
  const [email, setEmail] = React.useState("");

  React.useEffect(() => {
    if (!courseId && courses[0]) setCourseId(courses[0].id);
  }, [courses, courseId]);

  function submit() {
    if (!courseId) return;
    onSubmit({
      course_id: courseId,
      earliest_time: earliest,
      latest_time: latest,
      min_players: Number(players),
      email: email || null,
    });
  }

  return (
    <div style={{
      background: "#fff", border: "1px solid var(--hair)", borderRadius: 14,
      padding: 14, marginBottom: 14,
    }}>
      <Field label="Course">
        <select value={courseId} onChange={e => setCourseId(e.target.value)} style={input}>
          {courses.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <Field label="From">
          <input type="time" value={earliest} onChange={e => setEarliest(e.target.value)} style={input}/>
        </Field>
        <Field label="Until">
          <input type="time" value={latest} onChange={e => setLatest(e.target.value)} style={input}/>
        </Field>
      </div>
      <Field label="Players">
        <div style={{ display: "flex", gap: 4 }}>
          {[1, 2, 3, 4].map(n => (
            <button
              key={n}
              onClick={() => setPlayers(n)}
              type="button"
              style={{
                flex: 1, height: 34, borderRadius: 8,
                background: n === players ? forest : "transparent",
                color: n === players ? cream : forest,
                border: n === players ? "none" : "1px solid var(--hair)",
                fontSize: 13, fontFamily: "var(--f-mono)", cursor: "pointer",
              }}
            >{n}</button>
          ))}
        </div>
      </Field>
      <Field label="Email (optional)">
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="you@example.com"
          style={input}
        />
      </Field>
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <button onClick={submit} style={btnPrimary}>Create</button>
        <button onClick={onCancel} style={btnGhost}>Cancel</button>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label style={{ display: "block", marginBottom: 10 }}>
      <div className="eyebrow" style={{ marginBottom: 4 }}>{label}</div>
      {children}
    </label>
  );
}

const input = {
  width: "100%", height: 36, padding: "0 10px", borderRadius: 8,
  border: "1px solid var(--hair-strong)", background: "var(--cream-50)",
  fontFamily: "var(--f-ui)", fontSize: 13, color: forest, boxSizing: "border-box",
};
const btnGhost = {
  background: "transparent", border: "1px solid var(--hair-strong)",
  padding: "6px 12px", borderRadius: 8, fontSize: 12, color: forest,
  display: "flex", alignItems: "center", gap: 6, cursor: "pointer",
};
const btnPrimary = {
  background: forest, color: cream, border: "none",
  padding: "8px 14px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer",
  flex: 1,
};
const dim = { fontSize: 13, color: "var(--forest-600)", padding: "10px 0" };
const errStyle = {
  fontSize: 12, color: "var(--signal-red)", padding: "8px 10px",
  background: "rgba(248,113,113,0.08)", borderRadius: 8, marginBottom: 10,
};
