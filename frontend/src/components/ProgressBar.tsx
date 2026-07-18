'use client';

const STEPS = ['Info', 'Upload', 'Review', 'Pay', 'Letters'];

export function ProgressBar({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-1 mb-7">
      {STEPS.map((label, i) => {
        const step = i + 1;
        const isDone = step < current;
        const isActive = step === current;
        return (
          <div key={step} className="flex flex-col items-center flex-1 relative">
            {step < STEPS.length && (
              <div
                className={`absolute top-3.5 left-[60%] w-[80%] h-0.5 -z-10 transition-colors ${
                  isDone ? 'bg-purple-500 shadow-[0_0_6px_rgba(168,85,200,0.3)]' : 'bg-white/[0.06]'
                }`}
              />
            )}
            <div
              className={`w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                isActive
                  ? 'border-teal-400 bg-teal-400/[0.08] text-teal-400 shadow-[0_0_14px_rgba(0,212,212,0.4)]'
                  : isDone
                  ? 'border-purple-500 bg-purple-500/10 text-purple-400 shadow-[0_0_10px_rgba(168,85,200,0.3)]'
                  : 'border-white/10 bg-[#0A0A10] text-gray-600'
              }`}
            >
              {isDone ? '✓' : step}
            </div>
            <span
              className={`text-[9px] uppercase tracking-wide mt-1 text-center ${
                isActive ? 'text-teal-400' : isDone ? 'text-purple-400' : 'text-gray-600'
              }`}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
