"use client";

import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "";

export default function AdminPanel() {
  const [authed, setAuthed] = useState(false);
  const [adminKey, setAdminKey] = useState("");
  const [password, setPassword] = useState("");
  const [stats, setStats] = useState(null);
  const [lookupId, setLookupId] = useState("");
  const [lookupResult, setLookupResult] = useState(null);

  function login() {
    setAdminKey(password);
    setAuthed(true);
  }

  useEffect(() => {
    if (!authed) return;
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [authed]);

  async function refresh() {
    try {
      const res = await fetch(`${API}/api/admin/stats`, {
        headers: { "X-Admin-Key": adminKey },
      });
      if (res.status === 401) {
        setAuthed(false);
        setAdminKey("");
        return;
      }
      if (res.ok) setStats(await res.json());
    } catch {}
  }

  async function lookup() {
    if (!lookupId.trim()) return;
    try {
      const res = await fetch(`${API}/api/case/${lookupId.trim()}/status`);
      setLookupResult(res.ok ? await res.json() : { error: "Not found" });
    } catch {
      setLookupResult({ error: "Failed" });
    }
  }

  if (!authed) {
    return (
      <div className="max-w-xs mx-auto mt-32 text-center">
        <div className="w-12 h-12 rounded-xl bg-gold flex items-center justify-center font-bold text-lacquer mx-auto mb-4">
          AE
        </div>
        <h1 className="text-xl font-bold mb-4 font-heading text-gold">Admin</h1>
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && login()}
          className="input-field text-center mb-3"
        />
        <button onClick={login} className="btn-gold w-full py-3">
          Go
        </button>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 font-heading text-gold">Dashboard</h1>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {[
            { label: "Total Cases", value: stats.total_cases },
            { label: "Paid", value: stats.paid_cases },
            { label: "Revenue", value: stats.revenue_estimate },
            { label: "Today", value: stats.today },
          ].map((s, i) => (
            <div key={i} className="card text-center">
              <div className="text-2xl font-bold text-gold">{s.value}</div>
              <div className="text-xs text-muted mt-1 font-body">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Fishbowl status */}
      {stats?.fishbowl && (
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-gold/60 uppercase tracking-wider mb-3 font-heading">
            Regional Queues
          </h2>
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(stats.fishbowl).map(([state, info]) => (
              <div key={state} className="card">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-ivory font-heading">{state}</span>
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      info.utilization > 80
                        ? "bg-crimson/10 text-crimson"
                        : info.utilization > 50
                        ? "bg-gold/10 text-gold"
                        : "bg-jade/10 text-jade"
                    }`}
                  >
                    {info.utilization}%
                  </span>
                </div>
                <div className="h-1.5 bg-lacquer rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      info.utilization > 80
                        ? "bg-crimson"
                        : info.utilization > 50
                        ? "bg-gold"
                        : "bg-jade"
                    }`}
                    style={{ width: `${Math.min(info.utilization, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-muted mt-1 font-body">
                  {info.current}/{info.limit}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Session lookup */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-gold/60 uppercase tracking-wider mb-3 font-heading">
          Look Up a Session
        </h2>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Paste session ID here"
            value={lookupId}
            onChange={(e) => setLookupId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && lookup()}
            className="input-field font-mono text-sm"
          />
          <button onClick={lookup} className="btn-gold">
            Go
          </button>
        </div>
        {lookupResult && (
          <div className="mt-3 card">
            {lookupResult.error ? (
              <p className="text-crimson text-sm">{lookupResult.error}</p>
            ) : (
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm font-body">
                {[
                  ["Name", lookupResult.name],
                  ["Email", lookupResult.email],
                  ["Created", lookupResult.created_at?.split("T")[0]],
                  ["Disputes", `${lookupResult.items_count} items`],
                  ["Letters", `${lookupResult.letters_count} generated`],
                  [
                    "Paid",
                    lookupResult.paid ? "YES" : "No",
                    lookupResult.paid ? "text-jade" : "text-crimson",
                  ],
                  [
                    "Emailed",
                    lookupResult.email_sent ? "YES" : "No",
                    lookupResult.email_sent ? "text-jade" : "text-muted",
                  ],
                ].map(([label, value, color], i) => (
                  <div key={i} className="contents">
                    <div className="text-muted/60">{label}</div>
                    <div className={color || "text-ivory"}>{value}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <button
        onClick={refresh}
        className="text-sm text-muted/50 hover:text-gold transition-colors font-body"
      >
        Refresh data
      </button>
    </div>
  );
}
