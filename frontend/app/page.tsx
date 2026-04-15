'use client'

import { useShojiNav } from '@/lib/shojiNav'

export default function Home() {
  const { navigateTo } = useShojiNav()

  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/seascape.jpg"
        alt=""
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          objectFit: 'cover',
          zIndex: 0,
        }}
      />

      <div
        style={{
          position: 'relative',
          zIndex: 10,
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '2rem',
          gap: '1.25rem',
        }}
      >
        <h1
          style={{
            fontFamily: 'var(--font-cinzel-decorative), serif',
            fontSize: 'clamp(2rem, 5vw, 3.4rem)',
            color: '#F0D080',
            textShadow: '0 0 40px rgba(240,208,128,0.5), 0 2px 10px rgba(0,0,0,0.85)',
            letterSpacing: 4,
            lineHeight: 1.1,
            margin: 0,
          }}
        >
          BitmojiGuy 5 Min CreditFix
        </h1>

        <p
          style={{
            fontFamily: 'var(--font-cinzel), serif',
            fontSize: 'clamp(1rem, 2vw, 1.4rem)',
            color: '#F5E6C8',
            letterSpacing: 3,
            textShadow: '0 2px 10px rgba(0,0,0,0.85)',
            margin: 0,
          }}
        >
          5 Min. 5 Clicks. It&apos;s Fixed.
        </p>

        <div
          style={{
            marginTop: '1rem',
            padding: '0.85rem 1.6rem',
            border: '1px solid #F0D080',
            borderRadius: 4,
            background: 'rgba(10,6,2,0.55)',
            backdropFilter: 'blur(3px)',
            boxShadow: '0 4px 24px rgba(0,0,0,0.6)',
          }}
        >
          <p
            style={{
              fontFamily: 'var(--font-cinzel), serif',
              fontSize: 10,
              color: '#C9A84C',
              letterSpacing: 3,
              textTransform: 'uppercase',
              margin: 0,
              marginBottom: 4,
            }}
          >
            One Time
          </p>
          <p
            style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: '2.2rem',
              color: '#F0D080',
              letterSpacing: 2,
              lineHeight: 1,
              margin: 0,
              textShadow: '0 0 20px rgba(240,208,128,0.4)',
            }}
          >
            $24.99
          </p>
        </div>

        <button
          onClick={() => navigateTo('/map')}
          style={{
            marginTop: '1.5rem',
            fontFamily: 'var(--font-cinzel), serif',
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: 4,
            textTransform: 'uppercase',
            color: '#1A0A02',
            background: 'linear-gradient(135deg, #8B6914, #F0D080)',
            padding: '1rem 2.5rem',
            borderRadius: 4,
            border: '1px solid #8B5A20',
            cursor: 'pointer',
            boxShadow: '0 6px 30px rgba(201,168,76,0.45), inset 0 1px 0 rgba(255,255,255,0.25)',
            transition: 'all 0.2s',
          }}
        >
          Begin Your Credit Fix &rarr;
        </button>
      </div>
    </>
  )
}
