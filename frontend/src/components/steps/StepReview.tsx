'use client';

import { useState } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { confirmDisputes, ApiError } from '@/lib/api';
import { BUCKET_LABELS } from '@/lib/types';
import type { DisputeItemInput, Suggestion } from '@/lib/types';

interface Props {
  sessionId: string;
  suggestions: Suggestion[];
  onComplete: (itemsCount: number) => void;
}

interface CustomItem extends DisputeItemInput {
  bucket: string;
}

export function StepReview({ sessionId, suggestions, onComplete }: Props) {
  const [selected, setSelected] = useState<Set<number>>(new Set(suggestions.map((_, i) => i)));
  const [customItems, setCustomItems] = useState<CustomItem[]>([]);
  const [customTarget, setCustomTarget] = useState('');
  const [customAccount, setCustomAccount] = useState('');
  const [customReason, setCustomReason] = useState('');
  const [customType, setCustomType] = useState<'bureau' | 'creditor'>('bureau');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const bucketCounts: Record<string, number> = {};
  suggestions.forEach((s) => {
    bucketCounts[s.bucket] = (bucketCounts[s.bucket] || 0) + 1;
  });

  function toggleItem(i: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  function addCustom() {
    if (!customTarget.trim() || !customReason.trim()) {
      return setError('Custom disputes need at least a company name and a reason');
    }
    setError('');
    setCustomItems([
      ...customItems,
      {
        bucket: 'creditor_direct',
        type: customType,
        target: customTarget.trim(),
        account: customAccount.trim() || 'Unknown',
        reason: customReason.trim(),
      },
    ]);
    setCustomTarget('');
    setCustomAccount('');
    setCustomReason('');
  }

  async function handleSubmit() {
    const selectedItems: DisputeItemInput[] = suggestions
      .filter((_, i) => selected.has(i))
      .map((s) => ({
        type: s.type,
        target: s.target,
        account: s.account,
        amount: s.amount,
        opened: s.opened,
        reason: s.reason,
      }));
    const customInputs: DisputeItemInput[] = customItems.map((c) => ({
      type: c.type,
      target: c.target,
      account: c.account,
      reason: c.reason,
    }));
    const allItems = [...selectedItems, ...customInputs];
    if (!allItems.length) return setError('Select at least one dispute item');
    setError('');
    setLoading(true);
    try {
      const data = await confirmDisputes(sessionId, allItems);
      onComplete(data.items_count);
    } catch (e: unknown) {
      setError(e instanceof ApiError ? e.message : 'Failed — please try again');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-6 items-start">
      <BitmojiFigure pose="pointing" />
      <div className="flex-1 min-w-0">
        <Card className="!bg-[rgba(6,18,20,0.95)] !border-teal-400/15 !shadow-[0_0_30px_rgba(0,220,210,0.05)]">
          <CardTitle className="!text-teal-300 !drop-shadow-[0_0_14px_rgba(0,220,210,0.4)]">
            Review Disputes
          </CardTitle>
          <CardSub>We scanned your report for these issues. Select the ones to dispute.</CardSub>

          {/* Scan summary */}
          <div className="bg-green-400/[0.04] border border-green-400/15 rounded-xl p-5 mb-5">
            <h3 className="font-bangers text-[22px] text-green-400 drop-shadow-[0_0_10px_rgba(0,255,136,0.3)] mb-2 tracking-wide">
              Scan Complete
            </h3>
            {suggestions.length === 0 ? (
              <p className="text-sm text-gray-500">
                No issues auto-detected. Add dispute items manually below.
              </p>
            ) : (
              <>
                <p className="text-sm mb-2.5">
                  {suggestions.length} issue{suggestions.length !== 1 ? 's' : ''} found in your report.
                </p>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(bucketCounts).map(([bucket, count]) => (
                    <span key={bucket} className="inline-block bg-teal-400/[0.06] border border-teal-400/15 rounded-md px-3 py-1.5 text-[13px] font-semibold text-teal-400">
                      {BUCKET_LABELS[bucket] || bucket}: {count}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Detected dispute items */}
          <div className="space-y-2.5">
            {suggestions.map((item, i) => {
              const isSelected = selected.has(i);
              return (
                <div
                  key={i}
                  onClick={() => toggleItem(i)}
                  className={`flex items-center gap-3 rounded-lg px-4 py-3.5 cursor-pointer transition-all ${
                    isSelected
                      ? 'border border-teal-400/40 bg-teal-400/[0.06] shadow-[0_0_10px_rgba(0,220,210,0.08)]'
                      : 'border border-white/[0.06] bg-white/[0.02]'
                  }`}
                >
                  <div className={`w-[22px] h-[22px] rounded-md border-2 flex items-center justify-center text-xs shrink-0 transition-all ${
                    isSelected ? 'bg-teal-400/80 border-teal-400/80 text-white shadow-[0_0_8px_rgba(0,220,210,0.4)]' : 'border-white/10'
                  }`}>
                    {isSelected ? '✓' : ''}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm">
                      <strong>{item.target}</strong>
                      {item.account && item.account !== 'Unknown' && (
                        <span className="text-gray-500"> &middot; acct {item.account}</span>
                      )}
                      {item.amount != null && (
                        <span className="text-yellow-300"> &middot; ${item.amount.toFixed(2)}</span>
                      )}
                    </div>
                    <div className="text-[12px] text-gray-500 truncate">{item.reason}</div>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-teal-400/[0.08] text-teal-400 border border-teal-400/15 uppercase tracking-wide whitespace-nowrap">
                    {BUCKET_LABELS[item.bucket] || item.bucket}
                  </span>
                </div>
              );
            })}
            {customItems.map((item, i) => (
              <div key={`c${i}`} className="flex items-center gap-3 rounded-lg px-4 py-3.5 border border-teal-400/40 bg-teal-400/[0.06]">
                <div className="w-[22px] h-[22px] rounded-md bg-teal-400/80 border-2 border-teal-400/80 text-white flex items-center justify-center text-xs shrink-0">✓</div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm"><strong>{item.target}</strong>{item.account !== 'Unknown' && <span className="text-gray-500"> &middot; acct {item.account}</span>}</div>
                  <div className="text-[12px] text-gray-500 truncate">{item.reason}</div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/[0.08] text-purple-400 border border-purple-500/15 uppercase tracking-wide">Custom</span>
              </div>
            ))}
          </div>

          {/* Add custom dispute */}
          <div className="mt-5 border border-white/[0.06] rounded-xl p-4">
            <div className="text-[12px] font-bold uppercase tracking-wide text-gray-500 mb-3">
              Add something we missed
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[130px_1fr_1fr] gap-2 mb-2">
              <select
                value={customType}
                onChange={(e) => setCustomType(e.target.value as 'bureau' | 'creditor')}
                className="bg-[#0A0A10] text-gray-200 border border-teal-400/15 rounded-lg px-2.5 py-2.5 text-[13px]"
              >
                <option value="bureau">Bureau dispute</option>
                <option value="creditor">Creditor dispute</option>
              </select>
              <input
                value={customTarget}
                onChange={(e) => setCustomTarget(e.target.value)}
                placeholder={customType === 'bureau' ? 'Bureau (e.g. Experian)' : 'Creditor / collector name'}
                className="bg-teal-400/[0.03] border border-teal-400/15 rounded-lg px-3.5 py-2.5 text-[13px] text-gray-200 outline-none"
              />
              <input
                value={customAccount}
                onChange={(e) => setCustomAccount(e.target.value)}
                placeholder="Account # (optional)"
                className="bg-teal-400/[0.03] border border-teal-400/15 rounded-lg px-3.5 py-2.5 text-[13px] text-gray-200 outline-none"
              />
            </div>
            <div className="flex gap-2">
              <input
                value={customReason}
                onChange={(e) => setCustomReason(e.target.value)}
                placeholder="Why is this item wrong?"
                className="flex-1 bg-teal-400/[0.03] border border-teal-400/15 rounded-lg px-3.5 py-2.5 text-[13px] text-gray-200 outline-none"
                onKeyDown={(e) => e.key === 'Enter' && addCustom()}
              />
              <Button variant="ghost" onClick={addCustom}>Add</Button>
            </div>
          </div>

          {error && <p className="text-sm text-red-400 mt-3" role="alert">{error}</p>}
          <Button full onClick={handleSubmit} disabled={loading} className="mt-5">
            {loading ? 'Saving...' : 'Confirm My Disputes'}
          </Button>
        </Card>
      </div>
    </div>
  );
}
