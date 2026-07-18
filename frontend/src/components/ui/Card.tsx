export function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-[#0E0E16] border border-purple-500/15 rounded-xl p-7 mb-5 shadow-[0_0_30px_rgba(140,100,180,0.03)] ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <h2 className={`font-bangers text-[28px] tracking-wider text-purple-400 drop-shadow-[0_0_10px_rgba(168,85,200,0.3)] mb-1.5 ${className}`}>
      {children}
    </h2>
  );
}

export function CardSub({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-gray-500 mb-5">{children}</p>;
}
