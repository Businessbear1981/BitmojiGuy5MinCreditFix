'use client';

import { useState } from 'react';
import { Header } from '@/components/Header';
import { ProgressBar } from '@/components/ProgressBar';
import { StepInfo } from '@/components/steps/StepInfo';
import { StepUpload } from '@/components/steps/StepUpload';
import { StepReview } from '@/components/steps/StepReview';
import { StepPay } from '@/components/steps/StepPay';
import { StepLetters } from '@/components/steps/StepLetters';
import type { DisputeItem, ParsedDisputes } from '@/lib/types';

export default function Home() {
  const [step, setStep] = useState(1);
  const [parsed, setParsed] = useState<ParsedDisputes>({});
  const [items, setItems] = useState<DisputeItem[]>([]);
  const [letterCount, setLetterCount] = useState(0);

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
          Upload your credit report. We auto-detect problems, generate dispute letters for all 3 bureaus, and get you ready to mail in 5 minutes.
        </p>
      </section>

      {/* Main app */}
      <main className="relative z-[5] max-w-[720px] mx-auto px-5 pb-20">
        <ProgressBar current={step} />

        {step === 1 && <StepInfo onComplete={() => setStep(2)} />}
        {step === 2 && (
          <StepUpload
            onComplete={(p, i) => {
              setParsed(p);
              setItems(i);
              setStep(3);
            }}
          />
        )}
        {step === 3 && (
          <StepReview
            parsed={parsed}
            items={items}
            onComplete={(count) => {
              setLetterCount(count);
              setStep(4);
            }}
          />
        )}
        {step === 4 && <StepPay letterCount={letterCount} onComplete={() => setStep(5)} />}
        {step === 5 && <StepLetters />}
      </main>
    </>
  );
}
