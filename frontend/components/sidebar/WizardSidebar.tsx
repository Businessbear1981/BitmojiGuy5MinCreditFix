'use client'

import { useShojiNav } from '@/lib/shojiNav'
import { MrBeeks } from '@/components/mascot/MrBeeks'

const BEEKS_SIGNS: Record<number, string> = {
  1: 'Chart the course',
  2: 'Armor up!',
  3: 'Read the scrolls',
  4: 'Rake the sand',
  5: 'Pay the toll',
  6: 'Send the mail',
  7: 'Watch & wait',
}

const STEPS = [
  { n: 1, kanji: '地', label: 'Map',      route: '/map'       },
  { n: 2, kanji: '武', label: 'Dojo',     route: '/dojo'      },
  { n: 3, kanji: '水', label: 'Koi',      route: '/koi-pond'  },
  { n: 4, kanji: '庭', label: 'Garden',   route: '/garden'    },
  { n: 5, kanji: '階', label: 'Stairway', route: '/stairway'  },
  { n: 6, kanji: '門', label: 'Gate',     route: '/gate'      },
  { n: 7, kanji: '眼', label: 'Watcher',  route: '/watcher'   },
]

const STEP_COLORS = ['#C9A84C', '#1D9E75', '#7F77DD', '#EF9F27', '#5DCAA5', '#D94A3B', '#8CB4FF']

interface WizardSidebarProps {
  step: number
  mascotSpeech?: string
}

export function WizardSidebar({ step, mascotSpeech }: WizardSidebarProps) {
  const { navigateTo } = useShojiNav()

  return (
    <div style={{
      width: 180,
      minHeight: '100%',
      background: 'rgba(5,4,3,0.7)',
      backdropFilter: 'blur(6px)',
      borderRight: `1px solid rgba(201,168,76,0.12)`,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '2rem 1rem',
      gap: '1.5rem',
      flexShrink: 0,
    }}>
      {/* Mr Beeks mascot */}
      <MrBeeks signText={BEEKS_SIGNS[step]} />

      {/* Mascot speech */}
      {mascotSpeech && (
        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: 11,
          color: '#8A8278',
          textAlign: 'center',
          lineHeight: 1.5,
          fontStyle: 'italic',
        }}>
          {mascotSpeech}
        </p>
      )}

      {/* Step nav */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%' }}>
        {STEPS.map((s) => {
          const isDone = s.n < step
          const isCurrent = s.n === step
          const color = STEP_COLORS[s.n - 1]
          return (
            <button
              key={s.n}
              onClick={() => navigateTo(s.route)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 12px',
                borderRadius: 4,
                border: 'none',
                cursor: 'pointer',
                background: isCurrent ? `rgba(${
                  color === '#C9A84C' ? '201,168,76'
                  : color === '#1D9E75' ? '29,158,117'
                  : color === '#7F77DD' ? '127,119,221'
                  : color === '#EF9F27' ? '239,159,39'
                  : color === '#5DCAA5' ? '93,202,165'
                  : color === '#D94A3B' ? '217,74,59'
                  : color === '#8CB4FF' ? '140,180,255'
                  : '201,168,76'
                },0.1)` : 'transparent',
                transition: 'background 0.2s',
              }}
            >
              <span style={{
                fontFamily: 'serif',
                fontSize: 18,
                color: isDone ? '#1A6B4A' : isCurrent ? color : '#8A8278',
                opacity: isDone ? 0.7 : 1,
              }}>
                {isDone ? '✓' : s.kanji}
              </span>
              <span style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 11,
                letterSpacing: 1,
                textTransform: 'uppercase',
                color: isCurrent ? color : '#8A8278',
                opacity: isDone ? 0.5 : 1,
              }}>
                {s.label}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
