import Link from 'next/link';

export function Header() {
  return (
    <header className="relative z-10 flex items-center justify-between px-6 py-3.5 border-b border-purple-500/15 bg-black/85 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        {/* Stopwatch logo */}
        <div className="relative w-12 h-12 shrink-0">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-purple-500 rounded-sm shadow-[0_0_8px_rgba(168,85,200,0.6)]" />
          <div className="absolute bottom-0 left-0.5 w-11 h-11 rounded-full border-[2.5px] border-teal-400 bg-teal-400/[0.04] shadow-[0_0_20px_rgba(0,212,212,0.3),inset_0_0_12px_rgba(0,212,212,0.06)]" />
          <div className="absolute bottom-0 left-0.5 w-11 h-11 flex items-center justify-center font-bangers text-[30px] text-teal-400 leading-none drop-shadow-[0_0_12px_rgba(0,212,212,0.5)] pt-0.5">
            5
          </div>
        </div>
        <div className="flex flex-col">
          <span className="font-bangers text-[22px] tracking-wider text-teal-400 drop-shadow-[0_0_14px_rgba(0,212,212,0.4)] leading-tight">
            Min Credit <span className="text-yellow-300 drop-shadow-[0_0_14px_rgba(212,184,96,0.4)]">Fix</span>
          </span>
          <span className="text-[9px] font-bold tracking-[3px] uppercase text-gray-500">AE Labs</span>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Link
          href="/fishbowl"
          className="text-xs font-bold tracking-wider uppercase text-yellow-300 no-underline drop-shadow-[0_0_6px_rgba(212,184,96,0.3)] hover:text-yellow-200"
        >
          Learn
        </Link>
        <span className="text-[10px] font-bold tracking-wider text-gray-500 uppercase">AE.CC.001</span>
      </div>
    </header>
  );
}
