"use client";

import { useState } from "react";

const BUREAUS = ["Experian", "Equifax", "TransUnion"];

const BUCKETS = [
  {
    id: "collection",
    label: "Collection Accounts",
    desc: "Debts sold to collection agencies",
    icon: "!",
  },
  {
    id: "late_payment",
    label: "Late Payments",
    desc: "30/60/90/120 day late marks",
    icon: "\u23F0",
  },
  {
    id: "charge_off",
    label: "Charge-Offs",
    desc: "Accounts written off as bad debt",
    icon: "\u2716",
  },
  {
    id: "identity_error",
    label: "Not My Account",
    desc: "Accounts I don't recognize or didn't open",
    icon: "?",
  },
  {
    id: "inquiry",
    label: "Unauthorized Inquiries",
    desc: "Hard pulls I didn't approve",
    icon: "\uD83D\uDD0D",
  },
  {
    id: "medical_debt",
    label: "Medical Debt",
    desc: "Medical bills sent to collections",
    icon: "+",
  },
  {
    id: "obsolete",
    label: "Old / Expired Items",
    desc: "Negative items older than 7 years",
    icon: "\u231B",
  },
];

export default function StepDisputes({ api, sessionId, suggestions = [], onNext, onBack }) {
  const [selectedBuckets, setSelectedBuckets] = useState(new Set());
  const [items, setItems] = useState([]);
  const [phase, setPhase] = useState("select");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  function toggleBucket(id) {
    setSelectedBuckets((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function proceedToDetails() {
    const newItems = Array.from(selectedBuckets).map((bucketId) => {
      const bucket = BUCKETS.find((b) => b.id === bucketId);
      return {
        bucket: bucketId,
        type: bucketId === "creditor_direct" ? "creditor" : "bureau",
        target: "Experian",
        account: "",
        amount: "",
        reason: "",
        label: bucket?.label || bucketId,
      };
    });
    setItems(newItems);
    setPhase("details");
  }

  function updateItem(idx, field, value) {
    setItems((prev) => {
      const copy = [...prev];
      copy[idx] = { ...copy[idx], [field]: value };
      return copy;
    });
  }

  function addItemForBucket(bucketId) {
    const bucket = BUCKETS.find((b) => b.id === bucketId);
    setItems((prev) => [
      ...prev,
      {
        bucket: bucketId,
        type: "bureau",
        target: "Experian",
        account: "",
        amount: "",
        reason: "",
        label: bucket?.label || bucketId,
      },
    ]);
  }

  function removeItem(idx) {
    setItems((prev) => prev.filter((_, i) => i !== idx));
  }

  async function submit() {
    setSubmitting(true);
    setError("");
    try {
      const payload = items.map((it) => ({
        type: it.type,
        target: it.target,
        account: it.account,
        amount: it.amount ? parseFloat(it.amount) : null,
        opened: null,
        reason: it.reason || `Disputed under ${it.label}`,
      }));
      const res = await fetch(`${api}/api/case/${sessionId}/disputes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: payload }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to submit disputes");
      }
      onNext();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  // ─── Phase 1: Bucket selection ───
  if (phase === "select") {
    return (
      <div>
        <h2 className="step-header text-2xl font-bold mb-2">
          The Koi Pond
        </h2>
        <p className="text-muted mb-6 font-body">
          We&apos;ve analyzed your report and identified every error.
          Check everything you see on your credit report. We&apos;ll build the right
          dispute letters automatically.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {BUCKETS.map((bucket) => (
            <button
              key={bucket.id}
              onClick={() => toggleBucket(bucket.id)}
              className={`text-left p-4 rounded-lg border-2 transition-all font-body ${
                selectedBuckets.has(bucket.id)
                  ? "border-gold bg-gold/10"
                  : "border-gold-border bg-card hover:border-gold/40"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold ${
                    selectedBuckets.has(bucket.id)
                      ? "bg-gold text-lacquer"
                      : "bg-lacquer text-gold/40 border border-gold-border"
                  }`}
                >
                  {selectedBuckets.has(bucket.id) ? "\u2713" : bucket.icon}
                </div>
                <div>
                  <div
                    className={`font-medium font-heading text-sm ${
                      selectedBuckets.has(bucket.id)
                        ? "text-gold"
                        : "text-ivory"
                    }`}
                  >
                    {bucket.label}
                  </div>
                  <div className="text-xs text-muted">{bucket.desc}</div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* AI-detected suggestions */}
        {suggestions.length > 0 && (
          <div className="mt-6 msg-info">
            <h3 className="text-sm font-semibold text-gold mb-3 font-heading">
              AI Detected {suggestions.length} Disputable Item(s)
            </h3>
            <p className="text-xs text-muted mb-3 font-body">
              We scanned your credit report and found these items. Tap any to
              auto-select its category.
            </p>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => {
                    if (s.bucket && !selectedBuckets.has(s.bucket)) {
                      toggleBucket(s.bucket);
                    }
                  }}
                  className={`w-full text-left p-3 rounded-lg border text-xs transition-all font-body ${
                    selectedBuckets.has(s.bucket)
                      ? "border-gold/40 bg-gold/10"
                      : "border-gold-border bg-card hover:border-gold/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-ivory font-medium">
                      {s.target || "Unknown"} &mdash; {s.account || "N/A"}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs ${
                      s.confidence === "high"
                        ? "bg-jade/20 text-jade"
                        : s.confidence === "medium"
                        ? "bg-gold/20 text-gold"
                        : "bg-mist text-muted"
                    }`}>
                      {s.confidence || "low"}
                    </span>
                  </div>
                  <div className="text-muted mt-1">{s.reason}</div>
                  {s.amount && (
                    <div className="text-ivory/80 mt-0.5">${s.amount.toLocaleString()}</div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && <p className="mt-4 msg-error">{error}</p>}

        <div className="flex gap-3 mt-6">
          <button onClick={onBack} className="btn-ghost flex-1 py-3">
            Back
          </button>
          <button
            onClick={proceedToDetails}
            disabled={selectedBuckets.size === 0}
            className="btn-gold flex-1 py-3"
          >
            Next: Add Account Details
          </button>
        </div>
      </div>
    );
  }

  // ─── Phase 2: Account details ───
  return (
    <div>
      <h2 className="step-header text-2xl font-bold mb-2">Account Details</h2>
      <p className="text-muted mb-6 font-body">
        Enter the account info for each dispute. Every document strengthens
        your position.
      </p>

      <div className="space-y-5">
        {items.map((item, idx) => (
          <div key={idx} className="card space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gold font-heading">
                {item.label}
              </span>
              {items.length > 1 && (
                <button
                  onClick={() => removeItem(idx)}
                  className="text-xs text-crimson hover:text-crimson/80"
                >
                  Remove
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-muted mb-1 font-body">
                  Bureau / Creditor
                </label>
                <select
                  value={item.target}
                  onChange={(e) => updateItem(idx, "target", e.target.value)}
                  className="input-field text-sm"
                >
                  {BUREAUS.map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                  <option value="other">Other (type below)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-muted mb-1 font-body">
                  Account # / Name
                </label>
                <input
                  placeholder="e.g. Midland #12345"
                  value={item.account}
                  onChange={(e) => updateItem(idx, "account", e.target.value)}
                  className="input-field text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-muted mb-1 font-body">
                  Amount ($)
                </label>
                <input
                  type="number"
                  placeholder="0.00"
                  value={item.amount}
                  onChange={(e) => updateItem(idx, "amount", e.target.value)}
                  className="input-field text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1 font-body">
                  Extra Notes (optional)
                </label>
                <input
                  placeholder="Anything specific to add"
                  value={item.reason}
                  onChange={(e) => updateItem(idx, "reason", e.target.value)}
                  className="input-field text-sm"
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add more items */}
      <div className="mt-4 flex flex-wrap gap-2">
        {Array.from(selectedBuckets).map((bucketId) => {
          const bucket = BUCKETS.find((b) => b.id === bucketId);
          return (
            <button
              key={bucketId}
              onClick={() => addItemForBucket(bucketId)}
              className="px-3 py-1.5 border border-dashed border-gold-border rounded-lg text-xs text-muted hover:border-gold hover:text-gold transition-colors font-body"
            >
              + Another {bucket?.label}
            </button>
          );
        })}
      </div>

      {error && <p className="mt-4 msg-error">{error}</p>}

      <div className="flex gap-3 mt-6">
        <button onClick={() => setPhase("select")} className="btn-ghost flex-1 py-3">
          Back to Categories
        </button>
        <button
          onClick={submit}
          disabled={submitting || items.some((it) => !it.account)}
          className="btn-gold flex-1 py-3"
        >
          {submitting ? "Forging letters..." : "Forge My Dispute Letters"}
        </button>
      </div>
    </div>
  );
}
