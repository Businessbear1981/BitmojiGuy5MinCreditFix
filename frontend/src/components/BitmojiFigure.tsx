'use client';

type Pose = 'crossed' | 'reading' | 'pointing' | 'reviewing' | 'celebrating';

const POSE_LABELS: Record<Pose, string> = {
  crossed: 'Ready',
  reading: 'Reviewing',
  pointing: 'Targeting',
  reviewing: 'Almost There',
  celebrating: "Let's Go!",
};

export function BitmojiFigure({ pose }: { pose: Pose }) {
  return (
    <div className="w-[120px] shrink-0 text-center sticky top-[100px] hidden md:block">
      <div className="relative w-[70px] h-[110px] mx-auto mb-2">
        {/* Head */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-8 bg-[#D4A574] rounded-full shadow-[inset_-3px_-2px_0_rgba(0,0,0,0.1)]">
          <div className="absolute top-2.5 left-1/2 -translate-x-1/2 flex gap-2">
            <div className="w-1 h-1 bg-gray-800 rounded-full" />
            <div className="w-1 h-1 bg-gray-800 rounded-full" />
          </div>
        </div>
        {/* Hoodie */}
        <div className="absolute top-[30px] left-1/2 -translate-x-1/2 w-11 h-[38px] bg-[#1a1a1a] rounded-t-md rounded-b shadow-[inset_0_-4px_8px_rgba(0,0,0,0.3)]">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-2 bg-[#222] rounded-b-md" />
        </div>
        {/* Arms */}
        <Arms pose={pose} />
        {/* Jeans */}
        <div className="absolute top-[66px] left-1/2 -translate-x-1/2 w-10 h-8 bg-[#555] rounded-b">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-px h-full bg-black/15" />
        </div>
        {/* Shoes */}
        <div className="absolute top-[96px] left-1/2 -translate-x-1/2 flex gap-1.5">
          <div className="w-4 h-1.5 bg-[#222] rounded-full" />
          <div className="w-4 h-1.5 bg-[#222] rounded-full" />
        </div>
        {/* Celebration sparkles */}
        {pose === 'celebrating' && (
          <>
            <div className="absolute top-1 left-1 w-1.5 h-1.5 bg-yellow-300 rounded-full shadow-[0_0_6px_theme(colors.yellow.300)] animate-pulse" />
            <div className="absolute top-1 right-1 w-1.5 h-1.5 bg-yellow-300 rounded-full shadow-[0_0_6px_theme(colors.yellow.300)] animate-pulse delay-300" />
          </>
        )}
      </div>
      <span className="text-[10px] text-gray-500 uppercase tracking-wider">{POSE_LABELS[pose]}</span>
    </div>
  );
}

function Arms({ pose }: { pose: Pose }) {
  const armBase = 'absolute w-2 rounded bg-[#1a1a1a]';
  const handBase = 'absolute w-2 h-2 bg-[#D4A574] rounded-full';

  const styles: Record<Pose, { left: string; right: string }> = {
    crossed: {
      left: `${armBase} h-7 top-[34px] left-[12px] rotate-[30deg]`,
      right: `${armBase} h-7 top-[34px] right-[12px] -rotate-[30deg]`,
    },
    reading: {
      left: `${armBase} h-6 top-[36px] left-[8px] rotate-[50deg]`,
      right: `${armBase} h-6 top-[36px] right-[8px] -rotate-[50deg]`,
    },
    pointing: {
      left: `${armBase} h-6 top-[34px] left-[6px] rotate-[10deg]`,
      right: `${armBase} h-[30px] top-[28px] right-0 -rotate-[70deg]`,
    },
    reviewing: {
      left: `${armBase} h-[22px] top-[38px] left-[10px] rotate-[40deg]`,
      right: `${armBase} h-6 top-[36px] right-[8px] -rotate-[20deg]`,
    },
    celebrating: {
      left: `${armBase} h-[30px] top-[20px] left-[2px] -rotate-[30deg]`,
      right: `${armBase} h-[30px] top-[20px] right-[2px] rotate-[30deg]`,
    },
  };

  return (
    <>
      <div className={styles[pose].left}>
        <div className={`${handBase} ${pose === 'celebrating' ? '-top-1' : '-bottom-0.5'} left-0`} />
      </div>
      <div className={styles[pose].right}>
        <div className={`${handBase} ${pose === 'celebrating' ? '-top-1' : '-bottom-0.5'} right-0`} />
      </div>
    </>
  );
}
