'use client'

import { useShojiNav } from '@/lib/shojiNav'

const STEP_COLORS = ['#C9A84C', '#1D9E75', '#7F77DD', '#EF9F27', '#5DCAA5']

interface TopNavProps {
  currentStep?: number
}

export function TopNav({ currentStep }: TopNavProps) {
  const { navigateTo } = useShojiNav()

  const accentColor = currentStep ? STEP_COLORS[currentStep - 1] : '#C9A84C'

  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '10px 24px',
      borderBottom: '1px solid rgba(201,168,76,0.12)',
      background: 'rgba(5,4,3,0.92)',
      backdropFilter: 'blur(12px)',
      position: 'relative',
      zIndex: 40,
    }}>
      {/* LEFT — logo + text */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <svg width="38" height="44" viewBox="0 0 38 44" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="15" y="0" width="8" height="5" rx="1.5" fill="#C9A84C" />
          <rect x="16.5" y="5" width="5" height="3" rx="1" fill="#8B6914" />
          <rect x="5" y="6" width="6" height="3" rx="1" fill="#8B6914" transform="rotate(-30 5 6)" />
          <rect x="27" y="4" width="6" height="3" rx="1" fill="#8B6914" transform="rotate(30 27 4)" />
          <circle cx="19" cy="26" r="16.5" stroke="#C9A84C" strokeWidth="2" fill="rgba(5,4,3,0.9)" />
          <circle cx="19" cy="26" r="14" stroke="rgba(201,168,76,0.15)" strokeWidth="0.5" fill="none" />
          <line x1="19" y1="11.5" x2="19" y2="14" stroke="rgba(201,168,76,0.4)" strokeWidth="1.2" strokeLinecap="round" />
          <line x1="19" y1="38" x2="19" y2="40.5" stroke="rgba(201,168,76,0.25)" strokeWidth="1" strokeLinecap="round" />
          <line x1="33" y1="26" x2="35.5" y2="26" stroke="rgba(201,168,76,0.25)" strokeWidth="1" strokeLinecap="round" />
          <line x1="2.5" y1="26" x2="5" y2="26" stroke="rgba(201,168,76,0.25)" strokeWidth="1" strokeLinecap="round" />
          <line x1="19" y1="26" x2="19" y2="14.5" stroke="#F0D080" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="19" cy="26" r="2" fill="#C9A84C" />
          <text x="19" y="33" textAnchor="middle" fontFamily="'Cinzel Decorative', serif" fontSize="14" fontWeight="700" fill="#F0D080">5</text>
        </svg>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 0, lineHeight: 1.15 }}>
          <span style={{ fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '0.85rem', color: '#F0D080', letterSpacing: 1.5 }}>
            BitmojiGuy{' '}<span style={{ color: '#F0EBE0' }}>5 Min</span>
          </span>
          <span style={{ fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '0.65rem', color: '#C9A84C', letterSpacing: 2 }}>
            CreditFix&trade;
          </span>
          <span style={{ fontFamily: 'var(--font-rajdhani), sans-serif', fontSize: 7, color: '#8B6914', letterSpacing: 4, textTransform: 'uppercase' }}>
            Arden Edge Capital &middot; AE.CC.001
          </span>
        </div>
      </div>

      {/* CENTER — step dots (only when currentStep exists) */}
      {currentStep != null && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {[1, 2, 3, 4, 5].map((n) => {
            const isDone = n < currentStep
            const isCurrent = n === currentStep
            const color = STEP_COLORS[n - 1]

            return (
              <button
                key={n}
                onClick={() => navigateTo(`/step/${n}`)}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 12,
                  fontWeight: 700,
                  fontFamily: 'var(--font-heading)',
                  cursor: 'pointer',
                  transition: 'all 0.25s',
                  border: isDone
                    ? '2px solid #1A6B4A'
                    : isCurrent
                    ? `2px solid ${color}`
                    : '2px solid #8B6914',
                  background: isDone
                    ? '#1A6B4A'
                    : 'transparent',
                  color: isDone
                    ? '#F0EBE0'
                    : isCurrent
                    ? color
                    : '#8A8278',
                  boxShadow: isCurrent
                    ? `0 0 12px ${color}44`
                    : 'none',
                }}
              >
                {isDone ? '✓' : n}
              </button>
            )
          })}
        </div>
      )}

      {/* RIGHT — slogan */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
        <span style={{
          fontFamily: 'var(--font-heading)',
          fontSize: 10,
          letterSpacing: 3,
          textTransform: 'uppercase',
          color: accentColor,
          transition: 'color 0.4s',
        }}>
          5 Min &middot; 5 Clicks &middot; It&apos;s Fixed
        </span>
        <span style={{
          fontFamily: 'var(--font-body)',
          fontSize: 9,
          letterSpacing: 2,
          textTransform: 'uppercase',
          color: '#8A8278',
        }}>
          You&apos;re Welcome
        </span>
      </div>
    </nav>
  )
}
