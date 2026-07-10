'use client';

import { useState, useRef } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { uploadFiles } from '@/lib/api';
import type { DisputeItem, ParsedDisputes } from '@/lib/types';

interface Props {
  onComplete: (parsed: ParsedDisputes, items: DisputeItem[]) => void;
}

interface SlotConfig {
  key: string;
  icon: string;
  label: string;
  description: string;
  accept: string;
  examples: string;
}

const SLOTS: SlotConfig[] = [
  {
    key: 'gov_id',
    icon: '🪪',
    label: 'Government ID',
    description: "Driver's license or state-issued ID",
    accept: '.pdf,.png,.jpg,.jpeg',
    examples: "Driver's license, state ID, passport",
  },
  {
    key: 'proof_address',
    icon: '🏠',
    label: 'Proof of Address',
    description: 'Recent utility bill, phone bill, or bank statement',
    accept: '.pdf,.png,.jpg,.jpeg',
    examples: 'Electric bill, cell phone bill, bank or card statement',
  },
  {
    key: 'credit_report',
    icon: '📊',
    label: 'Credit Report',
    description: 'PDF from AnnualCreditReport.com',
    accept: '.pdf,.txt',
    examples: 'Equifax, Experian, or TransUnion PDF report',
  },
];

function UploadSlot({
  config,
  file,
  onFileSelect,
}: {
  config: SlotConfig;
  file: File | null;
  onFileSelect: (file: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) onFileSelect(f);
  }

  return (
    <div
      className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all relative ${
        file
          ? 'border-green-400/30 bg-green-400/[0.04]'
          : dragOver
          ? 'border-purple-400 bg-purple-500/[0.06]'
          : 'border-purple-700/25 hover:border-purple-400 hover:bg-purple-500/[0.03]'
      }`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept={config.accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFileSelect(f);
        }}
      />

      {file ? (
        <div className="flex items-center gap-3 text-left">
          <span className="text-3xl shrink-0">&#10003;</span>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-bold text-green-400 mb-0.5">{config.label}</div>
            <div className="text-[13px] text-gray-300 truncate">{file.name}</div>
            <div className="text-[11px] text-gray-500">{(file.size / 1024).toFixed(0)} KB</div>
          </div>
          <span className="text-green-400 text-xl drop-shadow-[0_0_8px_rgba(0,255,136,0.4)]">&#10003;</span>
        </div>
      ) : (
        <>
          <div className="text-4xl mb-2">{config.icon}</div>
          <div className="text-sm font-bold mb-1">{config.label}</div>
          <div className="text-[13px] text-gray-500 mb-2">{config.description}</div>
          <div className="text-[11px] text-gray-600 italic">{config.examples}</div>
        </>
      )}
    </div>
  );
}

export function StepUpload({ onComplete }: Props) {
  const [files, setFiles] = useState<Record<string, File | null>>({
    gov_id: null,
    proof_address: null,
    credit_report: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const allFilled = files.gov_id && files.proof_address && files.credit_report;
  const filledCount = Object.values(files).filter(Boolean).length;

  function setSlotFile(key: string, file: File) {
    setFiles((prev) => ({ ...prev, [key]: file }));
  }

  async function handleUpload() {
    if (!allFilled) return setError('All three documents are required before proceeding');
    setError('');
    setLoading(true);
    try {
      const allFiles = Object.values(files).filter(Boolean) as File[];
      const data = await uploadFiles(allFiles);
      onComplete(data.parsed_disputes, data.dispute_items);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-6 items-start">
      <BitmojiFigure pose="reading" />
      <div className="flex-1 min-w-0">
        <Card className="!bg-gradient-to-br !from-[rgba(30,10,40,0.95)] !to-[rgba(20,8,35,0.95)] !border-purple-700/20 !shadow-[0_0_40px_rgba(80,30,120,0.08)]">
          <CardTitle className="!text-purple-300 !drop-shadow-[0_0_14px_rgba(160,100,220,0.4)]">
            Upload Your Documents
          </CardTitle>
          <CardSub>
            We need three documents to process your dispute. All three are required.
          </CardSub>

          {/* AnnualCreditReport link */}
          <div className="bg-teal-400/[0.04] border border-teal-400/[0.12] rounded-lg px-4 py-3 mb-5 text-[13px] leading-relaxed">
            <strong className="text-teal-400">Don&apos;t have your credit report yet?</strong>{' '}
            Get all 3 bureau reports free at{' '}
            <a
              href="https://www.annualcreditreport.com"
              target="_blank"
              rel="noopener"
              className="text-yellow-300 underline font-bold"
            >
              AnnualCreditReport.com
            </a>{' '}
            &mdash; the only federally authorized source. Download as PDF.
          </div>

          {/* Progress indicator */}
          <div className="flex items-center gap-2 mb-5">
            <div className="flex-1 h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-teal-400 rounded-full transition-all duration-500 shadow-[0_0_8px_rgba(168,85,200,0.3)]"
                style={{ width: `${(filledCount / 3) * 100}%` }}
              />
            </div>
            <span className="text-[12px] font-bold text-gray-500">{filledCount}/3</span>
          </div>

          {/* Three upload slots */}
          <div className="space-y-4">
            {SLOTS.map((slot) => (
              <UploadSlot
                key={slot.key}
                config={slot}
                file={files[slot.key]}
                onFileSelect={(f) => setSlotFile(slot.key, f)}
              />
            ))}
          </div>

          {/* Required notice */}
          {!allFilled && (
            <div className="mt-4 text-[12px] text-gray-500 text-center">
              <span className="text-purple-400">*</span> All three documents required to proceed.
              Your files are encrypted and deleted immediately after scanning.
            </div>
          )}

          {error && <p className="text-sm text-red-400 mt-3">{error}</p>}
          <Button full onClick={handleUpload} disabled={loading || !allFilled} className="mt-4">
            {loading ? 'Scanning your documents...' : allFilled ? 'Scan My Report' : `Upload ${3 - filledCount} more document${3 - filledCount !== 1 ? 's' : ''}`}
          </Button>
        </Card>
      </div>
    </div>
  );
}
