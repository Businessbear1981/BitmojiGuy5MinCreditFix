'use client'

import { useShojiNav } from '@/lib/shojiNav'

export default function InterstitialPage() {
  const { navigateTo } = useShojiNav()

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--black)',
      color: 'var(--white)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'var(--font-heading)',
      gap: 32,
      padding: '2rem',
    }}>
      <p style={{ color: 'var(--gold)', fontSize: 24, letterSpacing: 2 }}>
        Phase 4 — Art of War Interstitial
      </p>
      <button
        onClick={() => navigateTo('/step/1')}
        style={{
          fontFamily: 'var(--font-heading), serif',
          fontSize: 15,
          letterSpacing: 3,
          textTransform: 'uppercase',
          color: '#050403',
          background: 'linear-gradient(135deg, #C9A84C, #8B6914)',
          padding: '14px 48px',
          borderRadius: 4,
          border: 'none',
          cursor: 'pointer',
          boxShadow: '0 4px 24px rgba(201,168,76,0.3)',
        }}
      >
        Enter the Dojo &rarr;
      </button>
    </div>
  )
}
