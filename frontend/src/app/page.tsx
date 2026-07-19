'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { ProgressBar } from '@/components/ProgressBar';
import { StepInfo } from '@/components/steps/StepInfo';
import { StepUpload } from '@/components/steps/StepUpload';
import { StepReview } from '@/components/steps/StepReview';
import { StepPay } from '@/components/steps/StepPay';
import { StepLetters } from '@/components/steps/StepLetters';
import { getCaseStatus } from '@/lib/api';
import { clearSession, loadSession, saveSession } from '@/lib/session';
import type { Suggestion } from '@/lib/types';

export default function Home() {
  const [step, setStep] = useState(1);
  const [sessionId, setSessionId] = useState('');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [resuming, setResuming] = useState(true);
  const [resumeNote, setResumeNote] = useState('');

  // Resume: handles both a page refresh mid-journey and the Stripe redirect
  // back (?session_id=...&paid=true). The session id lives in localStorage.
  useEffect(() => {
    async function resume() {
      const params = new URLSearchParams(window.location.search);
      const fromStripe = params.get('paid') === 'true';
      const sid = params.get('session_id') || loadSession();
      if (params.get('session_id')) saveSession(params.get('session_id')!);
      if (sid) {
        try {
          // After the Stripe redirect the webhook can lag a beat — poll briefly
          let status = await getCaseStatus(sid);
          if (fromStripe && !status.paid) {
            for (let i = 0; i < 5 && !status.paid; i++) {
              await new Promise((r) => setTimeout(r, 1500));
              status = await getCaseStatus(sid);
            }
          }
          setSessionId(sid);
          if (status.paid) {
            setStep(5);
          } else if (status.letters_count > 0 || status.items_count > 0) {
            setStep(4);
            if (fromStripe) setResumeNote('Payment was not completed — you can try again below.');
          } else if (status.docs_complete) {
            setStep(2);
            setResumeNote('Welcome back — please re-upload your documents to continue securely.');
          } else {
            setStep(2);
          }
        } catch {
          // Session expired (24h purge) or unknown — start fresh
          clearSession();
        }
      }
      setResuming(false);
    }
    resume();
  }, []);

  return (
    <>
      <Header />

      {/* Background effects */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute w-[120vw] h-[120vh] -top-[10vh] -left-[10vw] rounded-full opacity-[0.035] blur-[80px] animate-[drift_25s_linear_infinite] bg-[radial-gradient(ellipse,rgba(100,60,140,0.5),transparent_70%)]" />
        <div className="absolute w-[120vw] h-[120vh] -top-[10vh] -left-[10vw] rounded-full opacity-[0.035] blur-[80px] animate-[drift_32s_linear_infinite_reverse] bg-[radial-gradient(ellipse,rgba(60,50,80,0.4),transparent_70%)]" style={{ animationDelay: '-12s' }} />
      </div>
      <div className="fixed bottom-0 left-0 right-0 h-[40vh] pointer-events-none z-[1] bg-gradient-to-t from-black/60 to-transparent opacity-80" />

      {/* Hero */}
      <section className="relative z-[5] text-center py-12 px-6">
        <div className="text-[11px] font-bold tracking-[3px] uppercase text-purple-400 drop-shadow-[0_0_10px_rgba(168,85,200,0.4)] mb-3">
          Upload. Parse. Dispute. Done.
        </div>
        <h1 className="font-bangers text-[clamp(42px,7vw,80px)] leading-[0.95] tracking-wider text-gray-200 drop-shadow-[0_0_30px_rgba(0,212,212,0.3)] mb-4">
          Fix Your <span className="text-teal-400 drop-shadow-[0_0_20px_rgba(0,212,212,0.5)]">Credit</span> Now
        </h1>
        <p className="text-base text-gray-400/60 max-w-[500px] mx-auto leading-relaxed">
          Upload your credit report. We auto-detect problems, generate dispute letters
          for all 3 bureaus, and mail them for you — in 5 minutes.
        </p>
      </section>

      {/* Main app */}
      <main className="relative z-[5] max-w-[720px] mx-auto px-5 pb-20">
        <ProgressBar current={step} />

        {resumeNote && (
          <div className="bg-yellow-600/[0.06] border border-yellow-600/20 rounded-lg px-4 py-3 mb-5 text-[13px] text-yellow-200/80">
            {resumeNote}
          </div>
        )}

        {resuming ? (
          <div className="text-center py-16 text-sm text-gray-500">Loading...</div>
        ) : (
          <>
            {step === 1 && (
              <StepInfo
                onComplete={(sid) => {
                  setSessionId(sid);
                  setResumeNote('');
                  setStep(2);
                }}
              />
            )}
            {step === 2 && (
              <StepUpload
                sessionId={sessionId}
                onComplete={(sugg) => {
                  setSuggestions(sugg);
                  setResumeNote('');
                  setStep(3);
                }}
              />
            )}
            {step === 3 && (
              <StepReview
                sessionId={sessionId}
                suggestions={suggestions}
                onComplete={() => setStep(4)}
              />
            )}
            {step === 4 && (
              <StepPay
                sessionId={sessionId}
                onComplete={() => {
                  setResumeNote('');
                  setStep(5);
                }}
              />
            )}
            {step === 5 && <StepLetters sessionId={sessionId} />}
          </>
        )}
      </main>

      {/* Legal footer */}
      <footer className="relative z-[5] max-w-[720px] mx-auto px-5 pb-10 text-center text-[11px] text-gray-600 leading-relaxed">
        AE Labs is a self-help document preparation tool, not a law firm or credit
        repair organization; nothing here is legal advice. Your data is encrypted
        at rest and permanently deleted within 24 hours.
        <div className="mt-2 flex justify-center gap-4">
          <a href="/terms" className="underline hover:text-gray-400">Terms of Service</a>
          <a href="/privacy" className="underline hover:text-gray-400">Privacy Policy</a>
          <a href="/fishbowl" className="underline hover:text-gray-400">Learn</a>
        </div>
      </footer>
    </>
  );
}
