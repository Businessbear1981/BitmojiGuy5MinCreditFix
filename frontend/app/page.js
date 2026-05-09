"use client";

import { useState, useEffect } from "react";
import StepUpload from "../components/StepUpload";
import StepDisputes from "../components/StepDisputes";
import StepReview from "../components/StepReview";
import StepPayment from "../components/StepPayment";
import TermsGate from "../components/TermsGate";
import MrBeeks from "../components/MrBeeks";

const STEP_LABELS = [
  "The Dojo",
  "Koi Pond",
  "Sand Garden",
  "The Stairway",
];

const STEP_DESCRIPTIONS = [
  "Begin Your Training",
  "Upload Your Battle Plans",
  "Your Disputes, Prepared",
  "Release Your Authority",
];

const API = process.env.NEXT_PUBLIC_API_URL || "";

export default function Home() {
  const [step, setStep] = useState(-1); // -1 = hero landing
  const [sessionId, setSessionId] = useState(null);
  const [letters, setLetters] = useState([]);
  const [coverSheet, setCoverSheet] = useState("");
  const [paid, setPaid] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [resumeId, setResumeId] = useState("");
  const [resumeError, setResumeError] = useState("");
  const [termsToken, setTermsToken] = useState(null);
  const [showTerms, setShowTerms] = useState(false);

  // Check URL params for returning from Stripe
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get("session_id");
    const wasPaid = params.get("paid");
    const stepParam = params.get("step");
    if (sid) {
      setSessionId(sid);
      setTermsToken("returning");
      if (wasPaid === "true") {
        setPaid(true);
        setStep(3);
      } else if (stepParam) {
        setStep(parseInt(stepParam, 10));
      } else {
        setStep(0);
      }
    }
  }, []);

  function handleTermsAccept(token) {
    setTermsToken(token);
    setShowTerms(false);
    setStep(0);
  }

  function beginQuest() {
    setShowTerms(true);
  }

  async function resumeSession() {
    if (!resumeId.trim()) return;
    setResumeError("");
    try {
      const res = await fetch(`${API}/api/case/${resumeId.trim()}/status`);
      if (!res.ok) throw new Error("Session not found");
      const data = await res.json();
      setSessionId(data.session_id);
      setTermsToken("returning");
      setPaid(data.paid);
      if (data.paid) {
        setStep(3);
      } else if (data.letters_count > 0) {
        setStep(2);
      } else if (data.docs_complete) {
        setStep(1);
      } else {
        setStep(0);
      }
    } catch {
      setResumeError("Session not found. Check your session ID.");
    }
  }

  function next() {
    setStep((s) => Math.min(s + 1, 3));
  }
  function back() {
    setStep((s) => Math.max(s - 1, 0));
  }

  // ─── Hero Landing ───
  if (step === -1) {
    return (
      <div>
        {showTerms && (
          <TermsGate api={API} onAccept={handleTermsAccept} />
        )}

        {/* Hero Section */}
        <section className="text-center py-16 relative">
          {/* Mr. Beeks — center stage */}
          <div className="mb-8">
            <MrBeeks stage={0} size="large" />
          </div>

          <h1 className="mb-4">
            Become the Warrior<br />Your Credit Deserves
          </h1>
          <p className="text-xl font-body text-muted max-w-2xl mx-auto mb-3">
            Five minutes to dispute. A lifetime of freedom.
          </p>
          <p className="text-sm font-body text-muted/70 max-w-xl mx-auto mb-10 leading-relaxed">
            Your credit report contains errors. The bureaus know it. We know it.
            But they&apos;re counting on you to do nothing. Don&apos;t.
            We&apos;ve weaponized the law. Now it&apos;s your turn.
          </p>

          <button
            onClick={beginQuest}
            className="btn-gold text-lg px-10 py-4 mb-6"
          >
            Begin Your Quest
          </button>

          <p className="text-xs text-muted/50 font-body">
            No subscription. No hidden fees. $24.99 one-time.
          </p>
        </section>

        {/* Resume Session */}
        <div className="max-w-md mx-auto mt-8">
          <div className="card">
            <h3 className="step-sub text-lg font-semibold mb-2">
              Returning Warrior?
            </h3>
            <p className="text-sm text-muted mb-3 font-body">
              Enter your session ID to resume your quest.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Enter your session ID"
                value={resumeId}
                onChange={(e) => setResumeId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && resumeSession()}
                className="input-field font-mono text-sm"
              />
              <button
                onClick={resumeSession}
                className="btn-outline whitespace-nowrap"
              >
                Resume
              </button>
            </div>
            {resumeError && (
              <p className="mt-2 text-crimson text-sm">{resumeError}</p>
            )}
          </div>
        </div>

        {/* How It Works */}
        <section className="mt-16 max-w-2xl mx-auto">
          <h2 className="step-header text-center text-2xl mb-8">The Path of Five</h2>
          <div className="space-y-4">
            {[
              { icon: "道", title: "The Dojo", desc: "Enter your details. Every warrior starts here." },
              { icon: "鯉", title: "The Koi Pond", desc: "Upload your credit report. We read every line." },
              { icon: "庭", title: "The Sand Garden", desc: "Review your FCRA dispute letters, perfected by law." },
              { icon: "階", title: "The Stairway", desc: "A $24.99 investment in your freedom. Certified mail to all 3 bureaus." },
              { icon: "門", title: "The Dragon Gate", desc: "Victory awaits. Track your progress as bureaus respond." },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-4 card">
                <div className="w-12 h-12 rounded-lg bg-gold/10 border border-gold-border flex items-center justify-center text-gold text-lg flex-shrink-0 font-heading">
                  {item.icon}
                </div>
                <div>
                  <div className="font-heading text-gold text-sm font-semibold">{item.title}</div>
                  <div className="text-muted text-sm font-body">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    );
  }

  // ─── Active Quest (Steps 0-3) ───
  return (
    <div>
      {/* Warrior + Progress */}
      <div className="flex flex-col md:flex-row gap-8 mb-10">
        {/* Left: Mr. Beeks */}
        <div className="hidden md:flex items-center justify-center w-48 flex-shrink-0">
          <MrBeeks stage={step + 1} size="medium" />
        </div>

        {/* Center: Progress Path */}
        <div className="flex-1">
          <div className="flex justify-between mb-3">
            {STEP_LABELS.map((label, i) => (
              <div key={i} className="path-node">
                <div className={`path-circle ${
                  i < step ? "completed" : i === step ? "active" : "pending"
                }`}>
                  {i < step ? "\u2713" : i + 1}
                </div>
                <span className={`text-xs mt-1.5 font-heading ${
                  i <= step ? "text-gold/80" : "text-gold/30"
                }`}>
                  {label}
                </span>
              </div>
            ))}
          </div>
          <div className="h-1.5 bg-gold/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gold rounded-full transition-all duration-500"
              style={{
                width: `${(step / 3) * 100}%`,
                transitionTimingFunction: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
              }}
            />
          </div>
          <p className="text-center text-sm text-gold/60 mt-2 font-body">
            {STEP_DESCRIPTIONS[step]}
          </p>
        </div>
      </div>

      {/* Steps */}
      {step === 0 && (
        <StepUpload
          api={API}
          sessionId={sessionId}
          setSessionId={setSessionId}
          suggestions={suggestions}
          setSuggestions={setSuggestions}
          termsToken={termsToken}
          onNext={next}
        />
      )}
      {step === 1 && (
        <StepDisputes
          api={API}
          sessionId={sessionId}
          suggestions={suggestions}
          onNext={next}
          onBack={back}
        />
      )}
      {step === 2 && (
        <StepReview
          api={API}
          sessionId={sessionId}
          letters={letters}
          setLetters={setLetters}
          coverSheet={coverSheet}
          setCoverSheet={setCoverSheet}
          onNext={next}
          onBack={back}
        />
      )}
      {step === 3 && (
        <StepPayment
          api={API}
          sessionId={sessionId}
          paid={paid}
          setPaid={setPaid}
          onBack={back}
        />
      )}
    </div>
  );
}
