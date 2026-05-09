"use client";

import { useState, useEffect } from "react";

export default function StepReview({
  api,
  sessionId,
  letters,
  setLetters,
  coverSheet,
  setCoverSheet,
  onNext,
  onBack,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedIdx, setExpandedIdx] = useState(null);

  useEffect(() => {
    if (letters.length > 0) return;
    generateLetters();
  }, []);

  async function generateLetters() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${api}/api/case/${sessionId}/letters`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to generate letters");
      const data = await res.json();
      setLetters(data.letters);
      setCoverSheet(data.cover_sheet);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="step-header text-2xl font-bold mb-2">The Sand Garden</h2>
      <p className="text-muted mb-6 font-body">
        We&apos;ve analyzed your report and identified every error. Below are the
        disputes we&apos;ll send on your behalf. Review them. They&apos;re your voice,
        amplified by the law.
      </p>

      {loading && (
        <div className="text-center py-12 text-muted">
          <div className="inline-block w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mb-3" />
          <p className="font-body">Forging your dispute letters...</p>
          <p className="text-xs text-muted/60 mt-1 font-body">
            The bureaus will hear from you &mdash; clearly, professionally, powerfully.
          </p>
        </div>
      )}

      {error && <p className="mb-4 msg-error">{error}</p>}

      {/* Cover sheet */}
      {coverSheet && (
        <div className="mb-4">
          <button
            onClick={() =>
              setExpandedIdx(expandedIdx === "cover" ? null : "cover")
            }
            className="w-full text-left card hover:border-gold/40 transition-colors"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-gold font-heading">
                Master Cover Sheet
              </span>
              <span className="text-muted text-sm font-body">
                {expandedIdx === "cover" ? "Collapse" : "Expand"}
              </span>
            </div>
          </button>
          {expandedIdx === "cover" && (
            <pre className="mt-1 bg-card border border-gold-border border-t-0 rounded-b-xl p-4 text-xs text-ivory/80 whitespace-pre-wrap overflow-x-auto font-body">
              {coverSheet}
            </pre>
          )}
        </div>
      )}

      {/* Letters */}
      <div className="space-y-3">
        {letters.map((letter, idx) => (
          <div key={letter.id}>
            <button
              onClick={() =>
                setExpandedIdx(expandedIdx === idx ? null : idx)
              }
              className="w-full text-left card hover:border-gold/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium text-ivory font-heading">
                    {letter.target}
                  </span>
                  <span className="ml-2 text-xs text-muted font-body">
                    {letter.id}
                  </span>
                </div>
                <span className="text-muted text-sm font-body">
                  {expandedIdx === idx ? "Collapse" : "Expand"}
                </span>
              </div>
            </button>
            {expandedIdx === idx && (
              <pre className="mt-1 bg-card border border-gold-border border-t-0 rounded-b-xl p-4 text-xs text-ivory/80 whitespace-pre-wrap overflow-x-auto font-body">
                {letter.text}
              </pre>
            )}
          </div>
        ))}
      </div>

      {letters.length > 0 && !loading && (
        <div className="mt-4 msg-success text-sm">
          The letters are ready for release. {letters.length} dispute letter(s) forged.
        </div>
      )}

      <div className="flex gap-3 mt-6">
        <button onClick={onBack} className="btn-ghost flex-1 py-3">
          Back
        </button>
        <button
          onClick={onNext}
          disabled={letters.length === 0}
          className="btn-gold flex-1 py-3"
        >
          Proceed to Payment
        </button>
      </div>
    </div>
  );
}
