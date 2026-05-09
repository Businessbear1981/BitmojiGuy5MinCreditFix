"use client";

import { useState, useEffect } from "react";
import PartnerCards from "./PartnerCards";
import MrBeeks from "./MrBeeks";

export default function StepPayment({ api, sessionId, paid, setPaid, onBack }) {
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [tracking, setTracking] = useState(null);
  const [mailStatus, setMailStatus] = useState("");

  useEffect(() => {
    if (!paid) return;
    fetchTracking();
  }, [paid]);

  async function fetchTracking() {
    setMailStatus("sending");
    try {
      const res = await fetch(`${api}/api/case/${sessionId}/mail-status`);
      if (res.ok) {
        const data = await res.json();
        setTracking(data.tracking);
        setMailStatus(data.status);
      }
    } catch {
      setMailStatus("unknown");
    }
  }

  async function handleCheckout() {
    setProcessing(true);
    setError("");
    try {
      const res = await fetch(`${api}/api/case/${sessionId}/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error("Failed to create checkout");
      const data = await res.json();

      if (data.already_paid || data.demo_mode) {
        setPaid(true);
        return;
      }

      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  }

  function downloadLetters() {
    window.open(`${api}/api/case/${sessionId}/download`, "_blank");
  }

  return (
    <div>
      <h2 className="step-header text-2xl font-bold mb-2">
        The Stairway
      </h2>

      {!paid ? (
        <>
          <p className="text-muted mb-6 font-body">
            You&apos;ve prepared. Now you&apos;ll act. A $24.99 investment in your
            freedom. Your disputes will be sent to all three bureaus via
            certified mail, with proof of delivery and full legal backing.
          </p>

          <div className="card text-center max-w-lg mx-auto">
            <div className="text-5xl font-bold text-gold mb-1 font-display">$24.99</div>
            <p className="text-sm text-muted mb-6 font-body">
              One-time fee, no subscription
            </p>

            <div className="text-left max-w-sm mx-auto mb-6 space-y-2">
              {[
                "FCRA-compliant dispute letters for all 3 bureaus",
                "Direct creditor dispute letters",
                "Printed & mailed via USPS Certified Mail",
                "Return Receipt for legal proof of delivery",
                "Tracking numbers for every letter",
                "PDF copy emailed to you",
                "30-day deadline tracker",
              ].map((item, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 text-sm text-ivory/80 font-body"
                >
                  <span className="text-gold mt-0.5">&#10003;</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleCheckout}
              disabled={processing}
              className="btn-gold w-full max-w-sm py-3 text-lg"
            >
              {processing ? "Redirecting to checkout..." : "Authorize Payment — $24.99"}
            </button>

            <p className="text-xs text-muted/60 mt-3 font-body">
              Secure payment via Stripe. No recurring charges.
              By proceeding, you authorize us to send your dispute letters on your behalf.
            </p>
          </div>

          {error && <p className="mt-4 msg-error">{error}</p>}

          <div className="flex gap-3 mt-6">
            <button onClick={onBack} className="btn-ghost flex-1 py-3">
              Back
            </button>
          </div>
        </>
      ) : (
        <div className="py-8">
          {/* Victory — Dragon Gate */}
          <div className="text-center">
            <MrBeeks stage={5} size="large" />

            <h3 className="text-xl font-bold text-ivory mb-2 mt-6 font-heading">
              Victory Awaits — The Dragon Gate
            </h3>
            <p className="text-muted mb-6 font-body">
              Your disputes have been sent. The bureaus have 30 days to investigate.
              You&apos;ll receive their responses directly. This is where the real
              battle begins &mdash; and where you win.
            </p>
          </div>

          {/* Tracking */}
          {mailStatus === "sending" && (
            <div className="text-center py-6 text-muted">
              <div className="inline-block w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mb-3" />
              <p className="font-body">Preparing your certified mail...</p>
            </div>
          )}

          {tracking && tracking.length > 0 && (
            <div className="space-y-3 mb-6">
              <h4 className="step-sub font-semibold text-sm">
                Certified Mail Tracking
              </h4>
              {tracking.map((t, i) => (
                <div key={i} className="card">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-medium text-ivory font-heading">{t.target}</span>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-jade/10 text-jade">
                      {t.status}
                    </span>
                  </div>
                  {t.tracking_number && (
                    <p className="text-xs text-muted font-mono">
                      Tracking: {t.tracking_number}
                    </p>
                  )}
                  {t.expected_delivery && (
                    <p className="text-xs text-muted font-body">
                      Expected delivery: {t.expected_delivery}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {mailStatus === "unknown" && (
            <div className="card mb-6 text-center">
              <p className="text-sm text-muted font-body">
                Your letters are being processed. Tracking info will appear shortly.
              </p>
              <button
                onClick={fetchTracking}
                className="mt-2 text-sm text-gold hover:text-gold-light font-heading"
              >
                Refresh status
              </button>
            </div>
          )}

          {/* Download */}
          <div className="text-center mb-6">
            <button onClick={downloadLetters} className="btn-gold text-lg px-8 py-3">
              Download PDF Copy
            </button>
          </div>

          {/* What happens next */}
          <div className="card max-w-md mx-auto mb-6">
            <h4 className="step-sub font-medium mb-2 text-sm">
              What Happens Next
            </h4>
            <ol className="text-sm text-muted space-y-2.5 list-decimal list-inside font-body">
              <li>Watch for bureau responses (<span className="text-gold">30 days</span>)</li>
              <li>If they don&apos;t respond, that&apos;s a violation. We can help.</li>
              <li>If they respond but don&apos;t fix it, we escalate.</li>
              <li>Your credit improves. Your freedom grows.</li>
              <li>
                Check your updated reports at{" "}
                <a
                  href="https://www.annualcreditreport.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gold underline hover:text-gold-light"
                >
                  AnnualCreditReport.com
                </a>
              </li>
            </ol>
          </div>

          <p className="text-xs text-muted/50 text-center mb-10 font-body">
            Session ID:{" "}
            <code className="font-mono bg-card px-1 rounded">
              {sessionId}
            </code>{" "}
            &mdash; save this to check status anytime.
          </p>

          {/* Partner cards */}
          <div className="text-left max-w-2xl mx-auto mt-8 pt-8 border-t border-gold-border">
            <PartnerCards />
          </div>
        </div>
      )}
    </div>
  );
}
