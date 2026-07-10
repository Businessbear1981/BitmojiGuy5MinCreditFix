'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { getLetters } from '@/lib/api';
import type { Letter } from '@/lib/types';
import { DISPUTE_LABELS } from '@/lib/types';

export function StepLetters() {
  const [letters, setLetters] = useState<Letter[]>([]);
  const [confirmation, setConfirmation] = useState('---');
  const [types, setTypes] = useState<string[]>([]);
  const [filter, setFilter] = useState('all');
  const [countdown, setCountdown] = useState({ d: 30, h: 0, m: 0, s: 0, pct: 100 });

  const loadData = useCallback(async () => {
    try {
      const data = await getLetters();
      setLetters(data.letters);
      setConfirmation(data.confirmation);
      setTypes(data.dispute_types);
    } catch {
      // handled silently
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Countdown timer
  useEffect(() => {
    const stored = localStorage.getItem('ae_countdown_deadline');
    const deadline = stored ? new Date(stored) : new Date(Date.now() + 30 * 86400000);
    if (!stored) localStorage.setItem('ae_countdown_deadline', deadline.toISOString());
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
  }, []);

  const filtered = filter === 'all' ? letters : letters.filter((l) => l.type === filter);

  // Group by type
  const grouped: Record<string, Letter[]> = {};
  filtered.forEach((l) => {
    if (!grouped[l.type]) grouped[l.type] = [];
    grouped[l.type].push(l);
  });

  function copyLetter(body: string) {
    navigator.clipboard.writeText(body);
  }

  function downloadAll() {
    let text = '';
    letters.forEach((l, i) => {
      text += '='.repeat(70) + '\n';
      text += `LETTER ${i + 1}: ${l.title}\nBureau: ${l.bureau} | Address: ${l.bureau_address}\nType: ${l.type_label} | Variant: ${l.variant}\n`;
      text += '='.repeat(70) + '\n\n' + l.body + '\n\n\n';
    });
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'AE_Credit_Fix_Dispute_Letters.txt';
    a.click();
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
          <div className="font-mono text-xl font-bold text-yellow-600 tracking-[3px] drop-shadow-[0_0_8px_rgba(200,170,80,0.3)]">{confirmation}</div>
        </div>

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
            {countdown.d <= 0 ? 'Deadline reached. Send your 30-day follow-up letter.' : 'Bureaus must respond within 30 days of receiving your dispute.'}
          </div>
        </div>

        {/* Letters */}
        <Card className="!bg-[rgba(10,10,14,0.92)] !border-white/[0.08]">
          <CardTitle className="!text-white">Your Dispute Letters</CardTitle>
          <CardSub>Print each letter, sign it, and mail via certified mail to the address shown.</CardSub>

          {/* Filter tabs */}
          <div className="flex flex-wrap gap-2 mb-5">
            <button onClick={() => setFilter('all')} className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wide border transition-all cursor-pointer ${filter === 'all' ? 'bg-purple-500 border-purple-500 text-white shadow-[0_0_12px_rgba(168,85,200,0.3)]' : 'bg-transparent border-white/[0.08] text-gray-500 hover:border-purple-400 hover:text-purple-400'}`}>All</button>
            {types.map((t) => (
              <button key={t} onClick={() => setFilter(t)} className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wide border transition-all cursor-pointer ${filter === t ? 'bg-purple-500 border-purple-500 text-white' : 'bg-transparent border-white/[0.08] text-gray-500 hover:border-purple-400'}`}>
                {DISPUTE_LABELS[t] || t}
              </button>
            ))}
          </div>

          {/* Letter cards grouped */}
          {Object.entries(grouped).map(([type, group]) => (
            <div key={type} className="mb-6">
              <div className="font-bangers text-2xl text-yellow-600 tracking-wide mb-3 pb-2 border-b border-yellow-600/10 drop-shadow-[0_0_8px_rgba(200,170,80,0.2)]">
                {group[0]?.type_label}
              </div>
              {group.map((l, i) => (
                <div key={`${type}_${i}`} className="bg-[#06060C] border border-purple-500/15 rounded-xl p-5 mb-4">
                  <div className="flex justify-between items-center mb-3 flex-wrap gap-2">
                    <span className="font-bangers text-xl text-purple-400 tracking-wide drop-shadow-[0_0_8px_rgba(168,85,200,0.3)]">{l.bureau}</span>
                    <div>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-teal-400/[0.08] text-teal-400 border border-teal-400/15">Variant {l.variant}</span>
                      <span className="text-[11px] text-gray-500 ml-2">{l.title}</span>
                    </div>
                  </div>
                  <div className="text-[11px] text-gray-500 mb-2">Mail to: {l.bureau_address}</div>
                  <pre className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-5 text-[13px] leading-relaxed whitespace-pre-wrap font-sans max-h-[300px] overflow-y-auto">{l.body}</pre>
                  <div className="flex gap-2 mt-3">
                    <Button variant="ghost" onClick={() => copyLetter(l.body)}>Copy</Button>
                    <Button variant="ghost" onClick={() => { const w = window.open('','_blank'); w?.document.write(`<html><head><title>Dispute Letter</title><style>body{font-family:serif;font-size:14px;line-height:1.8;padding:40px;white-space:pre-wrap}</style></head><body>${l.body.replace(/</g,'&lt;')}</body></html>`); w?.document.close(); w?.print(); }}>Print</Button>
                  </div>
                </div>
              ))}
            </div>
          ))}

          <div className="flex gap-2.5 flex-wrap mt-5">
            <Button onClick={() => window.print()}>Print All</Button>
            <Button variant="ghost" onClick={downloadAll}>Download All as Text</Button>
          </div>
        </Card>

        {/* Next steps */}
        <Card className="!bg-[rgba(10,10,14,0.92)] !border-white/[0.08]">
          <CardTitle className="!text-white">Next Steps</CardTitle>
          <div className="text-sm leading-[1.8] text-gray-400">
            <strong>1.</strong> Print every letter above (or download the text file)<br />
            <strong>2.</strong> Sign and date each letter<br />
            <strong>3.</strong> Mail via <strong className="text-gray-200">certified mail with return receipt</strong> to each bureau address<br />
            <strong>4.</strong> Keep your certified mail receipts — this is your proof<br />
            <strong>5.</strong> Wait 30-45 days for bureau responses<br />
            <strong>6.</strong> If they don&apos;t respond or verify, file a CFPB complaint
          </div>
        </Card>
      </div>
    </div>
  );
}
