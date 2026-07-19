'use client';

import { useState, useEffect } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { getLetters, getMailStatus, downloadUrl } from '@/lib/api';
import type { GeneratedLetter, MailStatus } from '@/lib/types';

interface Props {
  sessionId: string;
}

export function StepLetters({ sessionId }: Props) {
  const [letters, setLetters] = useState<GeneratedLetter[]>([]);
  const [mail, setMail] = useState<MailStatus | null>(null);
  const [countdown, setCountdown] = useState({ d: 30, h: 0, m: 0, s: 0, pct: 100 });
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [lettersData, mailData] = await Promise.all([
          getLetters(sessionId),
          getMailStatus(sessionId).catch(() => null),
        ]);
        if (cancelled) return;
        setLetters(lettersData.letters);
        if (mailData) setMail(mailData);
      } catch {
        // transient — the retry button bumps reloadKey to re-fetch
      }
    })();
    return () => { cancelled = true; };
  }, [sessionId, reloadKey]);

  // Countdown timer — 30 days from purchase for the bureau response window
  useEffect(() => {
    const key = `cf_deadline_${sessionId}`;
    const stored = localStorage.getItem(key);
    const deadline = stored ? new Date(stored) : new Date(Date.now() + 30 * 86400000);
    if (!stored) localStorage.setItem(key, deadline.toISOString());
    const total = 30 * 86400000;

    const interval = setInterval(() => {
      const remaining = deadline.getTime() - Date.now();
      if (remaining <= 0) {
        setCountdown({ d: 0, h: 0, m: 0, s: 0, pct: 0 });
        clearInterval(interval);
        return;
      }
      setCountdown({
        d: Math.floor(remaining / 86400000),
        h: Math.floor((remaining % 86400000) / 3600000),
        m: Math.floor((remaining % 3600000) / 60000),
        s: Math.floor((remaining % 60000) / 1000),
        pct: Math.max(0, (remaining / total) * 100),
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [sessionId]);

  function copyLetter(body: string) {
    navigator.clipboard.writeText(body);
  }

  const pad = (n: number) => String(n).padStart(2, '0');

  return (
    <div className="flex gap-6 items-start">
      <BitmojiFigure pose="celebrating" />
      <div className="flex-1 min-w-0 relative">
        {/* Radial light burst */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-[radial-gradient(circle,rgba(255,255,255,0.06)_0%,rgba(255,255,255,0.02)_30%,transparent_70%)] pointer-events-none rounded-full -z-10" />

        {/* Confirmation */}
        <div className="text-center py-5 pb-7 relative z-10">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white/[0.08] border-2 border-white/30 shadow-[0_0_30px_rgba(255,255,255,0.1)] text-4xl mb-5">&#10003;</div>
          <div className="font-bangers text-[42px] tracking-wider text-white drop-shadow-[0_0_20px_rgba(255,255,255,0.3)] mb-2">You&apos;re All Set</div>
          <div className="text-[13px] text-gray-500 mb-1.5">CONFIRMATION</div>
          <div className="font-mono text-xl font-bold text-yellow-600 tracking-[3px] drop-shadow-[0_0_8px_rgba(200,170,80,0.3)]">{sessionId.toUpperCase()}</div>
          <div className="text-[11px] text-gray-500 mt-2 max-w-sm mx-auto">
            Save this code and download your PDF now — your data is permanently
            deleted from our servers within 24 hours.
          </div>
        </div>

        {/* Mail tracking */}
        <Card className="!bg-[rgba(10,10,14,0.92)] !border-white/[0.08]">
          <CardTitle className="!text-white">Mail Status</CardTitle>
          {mail && mail.tracking.length > 0 ? (
            <div className="space-y-2.5">
              {mail.tracking.map((t, i) => (
                <div key={i} className="flex items-center justify-between gap-3 rounded-lg px-4 py-3 border border-teal-400/15 bg-teal-400/[0.03] flex-wrap">
                  <div>
                    <div className="text-sm font-bold text-teal-400">{t.target}</div>
                    <div className="text-[12px] text-gray-500">{t.status}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-[12px] text-gray-300">{t.tracking_number}</div>
                    <div className="text-[11px] text-gray-500">Est. delivery {t.expected_delivery}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              {mail?.status === 'processing'
                ? 'Your letters are queued for mailing — tracking numbers will appear here.'
                : 'Mailing is being arranged. You can also print and mail the letters yourself below — send via certified mail and keep the receipts.'}
            </p>
          )}
        </Card>

        {/* Countdown */}
        <div className="bg-gradient-to-br from-teal-400/[0.05] to-purple-500/[0.04] border border-purple-500/15 rounded-xl p-7 text-center mb-5">
          <div className="text-[11px] uppercase tracking-[2px] text-gray-500 mb-3.5">Bureau Response Deadline</div>
          <div className="flex justify-center gap-4 mb-2">
            {[
              { val: countdown.d, label: 'Days' },
              { val: countdown.h, label: 'Hours' },
              { val: countdown.m, label: 'Min' },
              { val: countdown.s, label: 'Sec' },
            ].map((u) => (
              <div key={u.label} className="flex flex-col items-center">
                <div className="font-bangers text-5xl tracking-wider text-teal-400 leading-none min-w-[64px] drop-shadow-[0_0_12px_rgba(0,212,212,0.3)]">{pad(u.val)}</div>
                <div className="text-[10px] uppercase tracking-wider text-gray-500 mt-1">{u.label}</div>
              </div>
            ))}
          </div>
          <div className="w-full h-1.5 bg-white/[0.04] rounded-full mt-4 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-teal-400 to-purple-500 rounded-full shadow-[0_0_8px_rgba(0,212,212,0.3)] transition-all duration-1000" style={{ width: `${countdown.pct}%` }} />
          </div>
          <div className={`text-[12px] mt-2.5 ${countdown.d <= 5 ? 'text-yellow-300' : 'text-gray-500'}`}>
            {countdown.d <= 0
              ? 'Deadline reached. Re-run the flow to send your round-2 certified follow-up.'
              : 'Bureaus must respond within 30 days of receiving your dispute.'}
          </div>
        </div>

        {/* Letters */}
        <Card className="!bg-[rgba(10,10,14,0.92)] !border-white/[0.08]">
          <CardTitle className="!text-white">Your Dispute Letters</CardTitle>
          <CardSub>Download the signed-ready PDF packet, or copy/print individual letters.</CardSub>

          <div className="flex gap-2.5 flex-wrap mb-6">
            <a href={downloadUrl(sessionId)} download>
              <Button>Download PDF Packet</Button>
            </a>
            <Button variant="ghost" onClick={() => window.print()}>Print All</Button>
            {letters.length === 0 && (
              <Button variant="ghost" onClick={() => setReloadKey((k) => k + 1)}>Reload letters</Button>
            )}
          </div>

          {letters.map((ltr) => (
            <div key={ltr.id} className="bg-[#06060C] border border-purple-500/15 rounded-xl p-5 mb-4">
              <div className="flex justify-between items-center mb-3 flex-wrap gap-2">
                <span className="font-bangers text-xl text-purple-400 tracking-wide drop-shadow-[0_0_8px_rgba(168,85,200,0.3)]">{ltr.target}</span>
                {ltr.tracking_number && (
                  <span className="text-[11px] px-2 py-0.5 rounded bg-teal-400/[0.08] text-teal-400 border border-teal-400/15 font-mono">
                    {ltr.tracking_number}
                  </span>
                )}
              </div>
              <pre className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-5 text-[13px] leading-relaxed whitespace-pre-wrap font-sans max-h-[300px] overflow-y-auto">{ltr.text}</pre>
              <div className="flex gap-2 mt-3">
                <Button variant="ghost" onClick={() => copyLetter(ltr.text)}>Copy</Button>
                <Button variant="ghost" onClick={() => { const w = window.open('','_blank'); w?.document.write(`<html><head><title>Dispute Letter</title><style>body{font-family:serif;font-size:14px;line-height:1.8;padding:40px;white-space:pre-wrap}</style></head><body>${ltr.text.replace(/</g,'&lt;')}</body></html>`); w?.document.close(); w?.print(); }}>Print</Button>
              </div>
            </div>
          ))}
        </Card>

        {/* Next steps */}
        <Card className="!bg-[rgba(10,10,14,0.92)] !border-white/[0.08]">
          <CardTitle className="!text-white">Next Steps</CardTitle>
          <div className="text-sm leading-[1.8] text-gray-400">
            <strong>1.</strong> Download your PDF packet now (deleted from our servers in 24h)<br />
            <strong>2.</strong> Watch for mail tracking updates above<br />
            <strong>3.</strong> Bureaus have <strong className="text-gray-200">30 days</strong> to respond after receiving your dispute<br />
            <strong>4.</strong> Keep everything the bureaus mail back to you<br />
            <strong>5.</strong> No fix in 30 days? Re-run the flow — round 2 goes out via <strong className="text-gray-200">certified mail</strong><br />
            <strong>6.</strong> If they don&apos;t respond or verify, file a CFPB complaint
          </div>
        </Card>
      </div>
    </div>
  );
}
