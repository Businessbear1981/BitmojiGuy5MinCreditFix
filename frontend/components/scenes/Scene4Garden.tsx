export function Scene4Garden() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
      {/* Meshy 3D render background */}
      <img
        src="/scenes/scene4.png"
        alt=""
        style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'cover', objectPosition: 'center',
          filter: 'brightness(0.6) contrast(1.25) saturate(0.85)',
        }}
      />
      {/* Dark overlay */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(14,10,4,0.5)' }} />
      {/* SVG overlay — ominous garden details */}
      <svg width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice" style={{ position: 'absolute', inset: 0 }}>
        {/* Dark cloud mass upper left */}
        <path d="M0 20 Q60 10 120 30 Q180 15 240 35 Q300 20 340 40 Q300 60 240 50 Q180 65 120 48 Q60 58 0 45 Z" fill="#060408" opacity="0.6" />
        {/* Red star */}
        <circle cx="180" cy="45" r="1.5" fill="#8B1A1A" opacity="0.6" />
        {/* Disturbed rake lines */}
        <path d="M920 540 Q940 535 960 542 Q980 530 1000 538" fill="none" stroke="#1C1A10" strokeWidth="0.8" opacity="0.5" />
        <path d="M930 555 Q955 548 975 558 Q990 545 1010 552" fill="none" stroke="#1C1A10" strokeWidth="0.7" opacity="0.4" />
        <path d="M940 568 Q960 560 985 570 Q1005 558 1020 565" fill="none" stroke="#1A1810" strokeWidth="0.6" opacity="0.35" />
        {/* Claw marks */}
        <path d="M1040 535 Q1048 555 1042 575" fill="none" stroke="#1A1810" strokeWidth="1.2" opacity="0.3" strokeLinecap="round" />
        <path d="M1052 532 Q1058 552 1050 572" fill="none" stroke="#1A1810" strokeWidth="1" opacity="0.3" strokeLinecap="round" />
        <path d="M1064 530 Q1068 548 1060 568" fill="none" stroke="#1A1810" strokeWidth="0.8" opacity="0.3" strokeLinecap="round" />
      </svg>
    </div>
  )
}
