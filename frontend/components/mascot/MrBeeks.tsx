'use client'

interface MrBeeksProps {
  signText?: string
}

export function MrBeeks({ signText }: MrBeeksProps) {
  return (
    <div style={{ width: 120, height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <svg
        width="120"
        height="120"
        viewBox="0 0 120 120"
        style={{ animation: 'beeksBob 2.4s ease-in-out infinite' }}
      >
        {/* Shadow */}
        <ellipse cx="60" cy="112" rx="28" ry="3" fill="#000" opacity="0.25" />

        {/* Body — yellow circle */}
        <circle cx="60" cy="60" r="36" fill="#F5C842" stroke="#C4972F" strokeWidth="1.5" />
        {/* Body shading */}
        <path d="M40 46 Q60 34 80 46" fill="none" stroke="#FFE29A" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
        <ellipse cx="50" cy="54" rx="12" ry="8" fill="#FFE29A" opacity="0.4" />

        {/* Beak */}
        <path d="M54 66 L66 66 L72 74 L48 74 Z" fill="#F08040" stroke="#C05820" strokeWidth="1" strokeLinejoin="round" />
        <line x1="48" y1="70" x2="72" y2="70" stroke="#C05820" strokeWidth="0.8" />

        {/* Eyes — button style with highlights */}
        <circle cx="48" cy="54" r="5" fill="#1A1208" />
        <circle cx="46" cy="52" r="1.8" fill="#FFFFFF" />
        <circle cx="72" cy="54" r="5" fill="#1A1208" />
        <circle cx="70" cy="52" r="1.8" fill="#FFFFFF" />

        {/* Cheek blush */}
        <circle cx="38" cy="66" r="4" fill="#F5A0B0" opacity="0.5" />
        <circle cx="82" cy="66" r="4" fill="#F5A0B0" opacity="0.5" />

        {/* Legs — rust */}
        <rect x="46" y="92" width="4" height="14" fill="#C4724A" rx="1" />
        <rect x="70" y="92" width="4" height="14" fill="#C4724A" rx="1" />

        {/* Yellow boots */}
        <ellipse cx="48" cy="108" rx="7" ry="3.5" fill="#F5C842" stroke="#C4972F" strokeWidth="1" />
        <ellipse cx="72" cy="108" rx="7" ry="3.5" fill="#F5C842" stroke="#C4972F" strokeWidth="1" />
      </svg>

      {/* Sign text — small white card */}
      {signText && (
        <div style={{
          background: '#F0EBE0',
          color: '#1A1208',
          padding: '3px 8px',
          borderRadius: 3,
          fontFamily: 'var(--font-body), sans-serif',
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: 0.5,
          textAlign: 'center',
          boxShadow: '0 2px 4px rgba(0,0,0,0.25)',
          border: '1px solid #C4972F',
          maxWidth: 110,
          lineHeight: 1.2,
        }}>
          {signText}
        </div>
      )}

      <style>{`
        @keyframes beeksBob {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
      `}</style>
    </div>
  )
}
