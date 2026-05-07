'use client'

import { useShojiNav } from '@/lib/shojiNav'

const SCENES = [
  { route: '/map',      kanji: '地', element: 'Earth',   color: '#C9A84C' },
  { route: '/dojo',     kanji: '武', element: 'Warrior', color: '#33FFB8' },
  { route: '/koi-pond', kanji: '水', element: 'Water',   color: '#7F77DD' },
  { route: '/garden',   kanji: '庭', element: 'Garden',  color: '#EF9F27' },
  { route: '/stairway', kanji: '階', element: 'Ascent',  color: '#5CFFCC' },
  { route: '/gate',     kanji: '門', element: 'Gate',    color: '#D94A3B' },
  { route: '/watcher',  kanji: '眼', element: 'Sight',   color: '#8CB4FF' },
]

export default function Home() {
  const { navigateTo } = useShojiNav()

  return (
    <>
      <style>{`
        @keyframes orbitRing {
          from { transform: translate(-50%, -50%) rotate(0deg); }
          to   { transform: translate(-50%, -50%) rotate(360deg); }
        }
        @keyframes counterSpin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(-360deg); }
        }
        @keyframes satoriPulse {
          0%, 100% { opacity: 0.07; text-shadow: 0 0 60px rgba(201,168,76,0.35); }
          50%      { opacity: 0.11; text-shadow: 0 0 120px rgba(240,208,128,0.5); }
        }
        /* Mobile optimizations */
        @media (max-width: 768px) {
          .orbit-ring { animation-duration: 120s !important; }
          .scene-button { min-width: 48px; min-height: 48px; }
          .center-text { font-size: clamp(14px, 4vw, 24px); }
        }
      `}</style>

      {/* Lone Cypress Seascape — full bleed */}
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

      {/* 悟 — enlightenment watermark centered */}
      <div style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2,
        pointerEvents: 'none',
      }}>
        <span style={{
          fontFamily: 'serif',
          fontSize: 'min(55vmin, 680px)',
          color: '#C9A84C',
          lineHeight: 1,
          userSelect: 'none',
          animation: 'satoriPulse 8s ease-in-out infinite',
        }}>
          悟
        </span>
      </div>

      {/* Orbital ring — 7 scene kanji rotate around 悟 */}
      <div style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        width: 'min(78vmin, 720px)',
        height: 'min(78vmin, 720px)',
        animation: 'orbitRing 90s linear infinite',
        zIndex: 5,
        pointerEvents: 'none',
      }}>
        {SCENES.map((s, i) => {
          const angle = (i / SCENES.length) * 360
          const rad = (angle * Math.PI) / 180
          const xPct = Math.sin(rad) * 50
          const yPct = -Math.cos(rad) * 50
          const c = s.color
          return (
            <div
              key={s.route}
              style={{
                position: 'absolute',
                top: `calc(50% + ${yPct}%)`,
                left: `calc(50% + ${xPct}%)`,
                transform: 'translate(-50%, -50%)',
                pointerEvents: 'auto',
              }}
            >
              <button
                onClick={() => navigateTo(s.route)}
                style={{
                  animation: 'counterSpin 90s linear infinite',
                  width: 86,
                  height: 86,
                  borderRadius: '50%',
                  border: `1px solid ${c}AA`,
                  background: `radial-gradient(circle at 30% 25%, ${c}40, rgba(10,6,2,0.78))`,
                  backdropFilter: 'blur(4px)',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: `0 4px 24px rgba(0,0,0,0.6), 0 0 22px ${c}55`,
                  color: c,
                  transition: 'box-shadow 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = `0 4px 24px rgba(0,0,0,0.6), 0 0 42px ${c}CC`
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = `0 4px 24px rgba(0,0,0,0.6), 0 0 22px ${c}55`
                }}
              >
                <span style={{
                  fontFamily: 'serif',
                  fontSize: 28,
                  lineHeight: 1,
                  color: c,
                  textShadow: `0 0 18px ${c}99`,
                }}>
                  {s.kanji}
                </span>
                <span style={{
                  fontFamily: 'var(--font-cinzel), serif',
                  fontSize: 9,
                  letterSpacing: 2,
                  textTransform: 'uppercase',
                  color: c,
                  marginTop: 3,
                }}>
                  {s.element}
                </span>
              </button>
            </div>
          )
        })}
      </div>

      {/* Centered column */}
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
        {/* Stopwatch Logo */}
        <div style={{ marginBottom: '1rem', animation: 'pulse 3s ease-in-out infinite' }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.png" alt="BitmojiGuy 5 Min Credit Fix" style={{ height: 80, width: 80, filter: 'drop-shadow(0 0 20px rgba(201,168,76,0.4))' }} />
        </div>

        {/* Dark backdrop for text */}
        <div
          style={{
            background: 'linear-gradient(180deg, rgba(10,6,2,0.7), rgba(5,4,3,0.85))',
            backdropFilter: 'blur(8px)',
            padding: '2rem 2.5rem',
            borderRadius: 8,
            border: '1px solid rgba(201,168,76,0.2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(201,168,76,0.1)',
          }}
        >
            <h1
            style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: 'clamp(2rem, 5vw, 3.4rem)',
              color: '#F0D080',
              textShadow: '0 0 40px rgba(240,208,128,0.5), 0 0 20px rgba(201,168,76,0.3), 0 2px 10px rgba(0,0,0,0.9)',
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
              textShadow: '0 0 20px rgba(201,168,76,0.3), 0 2px 10px rgba(0,0,0,0.9)',
              margin: '0.5rem 0 0',
            }}
          >
            5 Min. 5 Clicks. It&apos;s Fixed.
          </p>
        </div>

        <div
          style={{
            marginTop: '1.5rem',
            padding: '0.85rem 1.6rem',
            border: '1px solid #F0D080',
            borderRadius: 4,
            background: 'rgba(10,6,2,0.55)',
            backdropFilter: 'blur(3px)',
            boxShadow: '0 4px 24px rgba(0,0,0,0.6)',
            transition: 'all 0.3s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = '0 8px 32px rgba(201,168,76,0.3), inset 0 1px 0 rgba(201,168,76,0.2)'
            e.currentTarget.style.transform = 'translateY(-4px)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = '0 4px 24px rgba(0,0,0,0.6)'
            e.currentTarget.style.transform = 'translateY(0)'
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

        {/* Video placeholders — BitmojiGuy (left) + Atom Adam (right) */}
        <div style={{
          display: 'flex',
          gap: '2rem',
          marginTop: '2rem',
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}>
          <div style={{
            width: 240,
            aspectRatio: '3 / 4',
            border: '1px solid #C9A84C',
            background: 'rgba(10,6,2,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#F0D080',
            fontFamily: 'var(--font-cinzel-decorative), serif',
            fontSize: 14,
            letterSpacing: 2,
            textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            backdropFilter: 'blur(3px)',
          }}>
            BitmojiGuy&trade; Intro
          </div>
          <div style={{
            width: 240,
            aspectRatio: '16 / 9',
            border: '1px solid #33FFB8',
            background: 'rgba(4,10,8,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#5CFFCC',
            fontFamily: 'var(--font-cinzel-decorative), serif',
            fontSize: 14,
            letterSpacing: 2,
            textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            backdropFilter: 'blur(3px)',
          }}>
            Atom Adam&trade;
          </div>
        </div>

        {/* Admin access */}
        <button
          onClick={() => navigateTo('/admin')}
          style={{
            marginTop: '2.5rem',
            fontFamily: 'var(--font-cinzel), serif',
            fontSize: 11,
            letterSpacing: 3,
            textTransform: 'uppercase',
            color: '#8A8278',
            background: 'transparent',
            padding: '8px 24px',
            borderRadius: 4,
            border: '1px solid rgba(138,130,120,0.25)',
            cursor: 'pointer',
            transition: 'all 0.3s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = '#C9A84C'
            e.currentTarget.style.borderColor = 'rgba(201,168,76,0.5)'
            e.currentTarget.style.textShadow = '0 0 10px rgba(201,168,76,0.4)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = '#8A8278'
            e.currentTarget.style.borderColor = 'rgba(138,130,120,0.25)'
            e.currentTarget.style.textShadow = 'none'
          }}
        >
          Admin Dashboard
        </button>
      </div>
    </>
  )
}
