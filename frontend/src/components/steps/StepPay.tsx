'use client';

import { useEffect, useState } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { createCheckout, generateLetters, ApiError } from '@/lib/api';
import { PRICE_DISPLAY } from '@/lib/types';
import type { GeneratedLetter } from '@/lib/types';

interface Props {
  sessionId: string;
  onComplete: () => void;
}

export function StepPay({ sessionId, onComplete }: Props) {
  const [letters, setLetters] = useState<GeneratedLetter[]>([]);
  const [generating, setGenerating] = useState(true);
  const [preview, setPreview] = useState<GeneratedLetter | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await generateLetters(sessionId);
        if (!cancelled) setLetters(data.letters);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof ApiError ? e.message : 'Could not generate letters — please try again');
      } finally {
        if (!cancelled) setGenerating(false);
      }
    })();
    return () => { cancelled = true; };
  }, [sessionId]);

  async function handlePay() {
    setLoading(true);
    setError('');
    try {
      const data = await createCheckout(sessionId);
      if (data.checkout_url) {
        // Session id is in localStorage — the journey resumes after Stripe redirects back
        window.location.href = data.checkout_url;
      } else if (data.paid || data.already_paid) {
        onComplete();
      }
    } catch (e: unknown) {
      setError(e instanceof ApiError ? e.message : 'Payment failed — please try again');
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-6 items-start">
      <BitmojiFigure pose="reviewing" />
      <div className="flex-1 min-w-0">
        <Card className="!bg-[rgba(24,22,20,0.95)] !border-yellow-600/12 !shadow-[0_0_30px_rgba(200,170,80,0.04)]">
          <CardTitle className="!text-yellow-600 !drop-shadow-[0_0_16px_rgba(200,170,80,0.4)]">
            Your Letters Are Ready
          </CardTitle>
          <CardSub>Review a preview below, then unlock and mail your dispute package.</CardSub>

          {/* Letter previews */}
          {generating ? (
            <div className="text-center py-8 text-sm text-gray-500">
              Generating your FCRA dispute letters...
            </div>
          ) : (
            <div className="space-y-2.5 mb-6">
              {letters.map((ltr) => (
                <div key={ltr.id} className="border border-white/[0.06] bg-white/[0.02] rounded-lg overflow-hidden">
                  <button
                    onClick={() => setPreview(preview?.id === ltr.id ? null : ltr)}
                    className="w-full flex items-center justify-between px-4 py-3 cursor-pointer text-left hover:bg-white/[0.02] transition-colors"
                  >
                    <span className="text-sm font-bold text-gray-200">Dispute Letter — {ltr.target}</span>
                    <span className="text-[11px] text-teal-400 uppercase tracking-wide">
                      {preview?.id === ltr.id ? 'Hide preview' : 'Preview'}
                    </span>
                  </button>
                  {preview?.id === ltr.id && (
                    <div className="relative border-t border-white/[0.06]">
                      <pre className="p-4 text-[12px] leading-relaxed whitespace-pre-wrap font-sans max-h-[220px] overflow-hidden text-gray-400">
                        {ltr.text.slice(0, 600)}
                      </pre>
                      {/* Fade-out — full letters unlock after payment */}
                      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[rgba(24,22,20,0.98)] to-transparent flex items-end justify-center pb-3">
                        <span className="text-[11px] text-yellow-600 uppercase tracking-wider font-bold">
                          Full letter unlocks after payment
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Price display */}
          <div className="text-center py-7 bg-yellow-600/[0.04] border border-yellow-600/12 rounded-xl mb-6">
            <div className="font-bangers text-7xl text-yellow-600 tracking-wider leading-none drop-shadow-[0_0_20px_rgba(200,170,80,0.4)]">
              {PRICE_DISPLAY}
            </div>
            <div className="text-[13px] text-gray-500 mt-1.5">One-time payment &middot; No subscription</div>
            <ul className="text-[12px] text-gray-500 mt-3 space-y-1 text-left max-w-xs mx-auto">
              <li><span className="text-green-400">&#10003;</span> {letters.length || 'Personalized'} dispute letter{letters.length !== 1 ? 's' : ''} with FCRA legal citations</li>
              <li><span className="text-green-400">&#10003;</span> Mailed to the bureaus for you (First Class, round 1)</li>
              <li><span className="text-green-400">&#10003;</span> Print-ready PDF packet emailed to you</li>
              <li><span className="text-green-400">&#10003;</span> Escalating postage ladder on follow-up rounds</li>
            </ul>
          </div>

          {error && <p className="text-sm text-red-400 mb-3" role="alert">{error}</p>}
          {!generating && letters.length === 0 && !error && (
            <p className="text-sm text-yellow-300 mb-3">No letters were generated — go back and confirm at least one dispute.</p>
          )}
          <Button
            full
            onClick={handlePay}
            disabled={loading || generating || letters.length === 0}
            className="!bg-gradient-to-br !from-yellow-600 !to-yellow-700 !shadow-[0_4px_24px_rgba(200,170,80,0.25)]"
          >
            {loading ? 'Connecting to secure checkout...' : `Pay ${PRICE_DISPLAY} — Mail My Letters`}
          </Button>

          <p className="text-center text-[11px] text-gray-500 mt-3">
            Secure payment via Stripe. Your data is encrypted and deleted within 24 hours.
          </p>
        </Card>
      </div>
    </div>
  );
}
