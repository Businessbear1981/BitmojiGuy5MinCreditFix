'use client'

import { useShojiNav } from '@/lib/shojiNav'
import { MrBeeks } from '@/components/mascot/MrBeeks'

const BEEKS_SIGNS: Record<number, string> = {
  1: 'Name your enemy',
  2: 'Armor up!',
  3: 'Read the scrolls',
  4: 'Pay the toll',
  5: 'You did it!',
}

const STEPS = [
  { n: 1, kanji: '武', label: 'Warrior' },
  { n: 2, kanji: '水', label: 'Water' },
  { n: 3, kanji: '智', label: 'Wisdom' },
  { n: 4, kanji: '金', label: 'Gold' },
  { n: 5, kanji: '涅', label: 'Nirvana' },
]

const STEP_COLORS = ['#C9A84C', '#1D9E75', '#7F77DD', '#EF9F27', '#5DCAA5']

interface WizardSidebarProps {
  step: number
  accentColor: string
  mascotSpeech?: string
}

export function WizardSidebar({ step, accentColor, mascotSpeech }: WizardSidebarProps) {
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
              onClick={() => navigateTo(`/step/${s.n}`)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 12px',
                borderRadius: 4,
                border: 'none',
                cursor: 'pointer',
                background: isCurrent ? `rgba(${color === '#C9A84C' ? '201,168,76' : color === '#1D9E75' ? '29,158,117' : color === '#7F77DD' ? '127,119,221' : color === '#EF9F27' ? '239,159,39' : '93,202,165'},0.1)` : 'transparent',
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
