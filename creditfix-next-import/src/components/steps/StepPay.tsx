'use client';

import { useState } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { createCheckout, manualPay } from '@/lib/api';

interface Props {
  letterCount: number;
  onComplete: () => void;
}

type PayMethod = 'card' | 'cashapp' | 'chime' | null;

export function StepPay({ letterCount, onComplete }: Props) {
  const [method, setMethod] = useState<PayMethod>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleCardPay() {
    setLoading(true);
    try {
      const data = await createCheckout();
      if (data.dev_mode) {
        onComplete();
      } else if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Payment failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleManualPay() {
    if (!method) return;
    setLoading(true);
    try {
      await manualPay(method);
      onComplete();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Payment failed');
    } finally {
      setLoading(false);
    }
  }

  function copyTag(text: string) {
    navigator.clipboard.writeText(text);
  }

  const methods: Array<{ id: PayMethod; icon: string; name: string; tag: string; detail?: string; copyValue?: string }> = [
    { id: 'card', icon: '💳', name: 'Card', tag: 'Visa, Mastercard, etc.' },
    { id: 'cashapp', icon: '💵', name: 'Cash App', tag: 'Send $19.99', detail: '$AELabsCreditFix', copyValue: '$AELabsCreditFix' },
    { id: 'chime', icon: '🏦', name: 'Chime', tag: 'Send $19.99', detail: '$AELabsPay', copyValue: '$AELabsPay' },
  ];

  return (
    <div className="flex gap-6 items-start">
      <BitmojiFigure pose="reviewing" />
      <div className="flex-1 min-w-0">
        <Card className="!bg-[rgba(24,22,20,0.95)] !border-yellow-600/12 !shadow-[0_0_30px_rgba(200,170,80,0.04)]">
          <CardTitle className="!text-yellow-600 !drop-shadow-[0_0_16px_rgba(200,170,80,0.4)]">
            Unlock Your Letters
          </CardTitle>
          <CardSub>Your dispute letters are ready. Choose how to pay.</CardSub>

          {/* Price display */}
          <div className="text-center py-7 bg-yellow-600/[0.04] border border-yellow-600/12 rounded-xl mb-6">
            <div className="font-bangers text-7xl text-yellow-600 tracking-wider leading-none drop-shadow-[0_0_20px_rgba(200,170,80,0.4)]">$19.99</div>
            <div className="text-[13px] text-gray-500 mt-1.5">One-time payment &middot; No subscription</div>
            <ul className="text-[12px] text-gray-500 mt-3 space-y-1 text-left max-w-xs mx-auto">
              <li><span className="text-green-400">&#10003;</span> Personalized dispute letters for all 3 bureaus</li>
              <li><span className="text-green-400">&#10003;</span> {letterCount} letters generated</li>
              <li><span className="text-green-400">&#10003;</span> FCRA/FDCPA legal citations included</li>
              <li><span className="text-green-400">&#10003;</span> Print-ready &mdash; just sign and mail</li>
            </ul>
          </div>

          {/* Payment methods */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
            {methods.map((m) => (
              <button
                key={m.id}
                onClick={() => setMethod(m.id)}
                className={`bg-white/[0.02] border-2 rounded-xl px-4 py-5 text-center cursor-pointer transition-all ${
                  method === m.id
                    ? 'border-yellow-600/40 bg-yellow-600/[0.06] shadow-[0_0_20px_rgba(200,170,80,0.12)]'
                    : 'border-white/[0.06] hover:border-yellow-600/20'
                }`}
              >
                <span className="text-3xl block mb-2">{m.icon}</span>
                <div className="text-sm font-bold">{m.name}</div>
                <div className="text-[11px] text-gray-500">{m.tag}</div>
                {method === m.id && m.detail && (
                  <div className="mt-3 text-[13px]">
                    <div className="text-gray-400 mb-1">Send <strong>$19.99</strong> to:</div>
                    <button
                      onClick={(e) => { e.stopPropagation(); copyTag(m.copyValue!); }}
                      className="w-full bg-yellow-600/[0.04] border border-yellow-600/15 rounded-lg py-2.5 px-3 text-yellow-600 font-mono text-[15px] tracking-wider text-center cursor-pointer hover:bg-yellow-600/[0.08] transition-all"
                    >
                      {m.detail}
                    </button>
                    <div className="text-[11px] text-gray-500 mt-1">Click to copy &middot; Include your email in the note</div>
                  </div>
                )}
              </button>
            ))}
          </div>

          {method === 'card' && (
            <Button full onClick={handleCardPay} disabled={loading}
              className="!bg-gradient-to-br !from-yellow-600 !to-yellow-700 !shadow-[0_4px_24px_rgba(200,170,80,0.25)]">
              {loading ? 'Connecting...' : 'Pay $19.99 with Card'}
            </Button>
          )}
          {(method === 'cashapp' || method === 'chime') && (
            <>
              <div className="bg-green-400/[0.04] border border-green-400/15 rounded-lg px-4 py-3.5 text-[13px] text-gray-400 mb-4">
                After sending payment, click below. We&apos;ll verify and unlock your letters.
              </div>
              <Button full onClick={handleManualPay} disabled={loading}
                className="!bg-gradient-to-br !from-yellow-600 !to-yellow-700">
                {loading ? 'Verifying...' : 'I Sent $19.99 — Unlock My Letters'}
              </Button>
            </>
          )}

          {error && <p className="text-sm text-red-400 mt-3">{error}</p>}
          <p className="text-center text-[11px] text-gray-500 mt-3">Your data is encrypted and never stored.</p>
        </Card>
      </div>
    </div>
  );
}
