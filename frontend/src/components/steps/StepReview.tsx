'use client';

import { useState } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { reviewDisputes } from '@/lib/api';
import { GILMORE_ORDER, GILMORE_PHASES, DISPUTE_LABELS } from '@/lib/types';
import type { DisputeItem, ParsedDisputes } from '@/lib/types';

interface Props {
  parsed: ParsedDisputes;
  items: DisputeItem[];
  onComplete: (letterCount: number) => void;
}

export function StepReview({ parsed, items, onComplete }: Props) {
  const sortedItems = [...items].sort(
    (a, b) => (GILMORE_ORDER.indexOf(a.type as typeof GILMORE_ORDER[number]) ?? 99) -
              (GILMORE_ORDER.indexOf(b.type as typeof GILMORE_ORDER[number]) ?? 99)
  );

  const [selected, setSelected] = useState<Set<number>>(new Set(sortedItems.map((_, i) => i)));
  const [customText, setCustomText] = useState('');
  const [customType, setCustomType] = useState('collections');
  const [customItems, setCustomItems] = useState<DisputeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const types = Object.keys(parsed).sort(
    (a, b) => (GILMORE_ORDER.indexOf(a as typeof GILMORE_ORDER[number]) ?? 99) -
              (GILMORE_ORDER.indexOf(b as typeof GILMORE_ORDER[number]) ?? 99)
  );
  const totalItems = Object.values(parsed).reduce((s, v) => s + v.items.length, 0);

  function toggleItem(i: number) {
    const next = new Set(selected);
    next.has(i) ? next.delete(i) : next.add(i);
    setSelected(next);
  }

  function addCustom() {
    if (!customText.trim()) return;
    setCustomItems([...customItems, { type: customType, label: DISPUTE_LABELS[customType] || customType, text: customText.trim() }]);
    setCustomText('');
  }

  async function handleSubmit() {
    const selectedItems = sortedItems.filter((_, i) => selected.has(i));
    if (!selectedItems.length && !customItems.length) return setError('Select at least one dispute item');
    setError('');
    setLoading(true);
    try {
      const data = await reviewDisputes(selectedItems, customItems);
      onComplete(data.letter_count);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed');
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
          <CardSub>We found these issues in your report. Select the ones to dispute.</CardSub>

          {/* Scan summary */}
          <div className="bg-green-400/[0.04] border border-green-400/15 rounded-xl p-5 mb-5">
            <h3 className="font-bangers text-[22px] text-green-400 drop-shadow-[0_0_10px_rgba(0,255,136,0.3)] mb-2 tracking-wide">
              Scan Complete &mdash; Gilmore Order
            </h3>
            {types.length === 0 ? (
              <p className="text-sm text-gray-500">No issues auto-detected. Add dispute items manually below.</p>
            ) : (
              <>
                <p className="text-sm mb-2.5">{totalItems} issue{totalItems !== 1 ? 's' : ''} found. Ordered for maximum impact.</p>
                <div className="flex flex-wrap gap-1">
                  {types.map((t) => (
                    <span key={t} className="inline-block bg-teal-400/[0.06] border border-teal-400/15 rounded-md px-3 py-1.5 text-[13px] font-semibold text-teal-400">
                      {GILMORE_PHASES[t] || parsed[t].label}: {parsed[t].items.length}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Dispute items */}
          <div className="space-y-2.5">
            {sortedItems.map((item, i) => {
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
                  <span className="text-sm flex-1">{item.text}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-teal-400/[0.08] text-teal-400 border border-teal-400/15 uppercase tracking-wide whitespace-nowrap">
                    {item.label}
                  </span>
                </div>
              );
            })}
            {customItems.map((item, i) => (
              <div key={`c${i}`} className="flex items-center gap-3 rounded-lg px-4 py-3.5 border border-teal-400/40 bg-teal-400/[0.06]">
                <div className="w-[22px] h-[22px] rounded-md bg-teal-400/80 border-2 border-teal-400/80 text-white flex items-center justify-center text-xs">✓</div>
                <span className="text-sm flex-1">{item.text}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-teal-400/[0.08] text-teal-400 border border-teal-400/15 uppercase tracking-wide">{item.label}</span>
              </div>
            ))}
          </div>

          {/* Add custom */}
          <div className="flex gap-2 mt-3">
            <select
              value={customType}
              onChange={(e) => setCustomType(e.target.value)}
              className="bg-[#0A0A10] text-gray-200 border border-teal-400/15 rounded-lg px-2.5 py-2.5 text-[13px]"
            >
              {Object.entries(DISPUTE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
            <input
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              placeholder="Add a custom dispute item..."
              className="flex-1 bg-teal-400/[0.03] border border-teal-400/15 rounded-lg px-3.5 py-2.5 text-[13px] text-gray-200 outline-none"
              onKeyDown={(e) => e.key === 'Enter' && addCustom()}
            />
            <Button variant="ghost" onClick={addCustom}>Add</Button>
          </div>

          {error && <p className="text-sm text-red-400 mt-3">{error}</p>}
          <Button full onClick={handleSubmit} disabled={loading} className="mt-5">
            {loading ? 'Generating...' : 'Generate My Letters'}
          </Button>
        </Card>
      </div>
    </div>
  );
}
