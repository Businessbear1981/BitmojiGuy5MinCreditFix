'use client'

import { ReactNode } from 'react'
import { PRESETS, ScenePresetKey } from './scenePresets'

interface SceneLayoutProps {
  preset: ScenePresetKey
  children: ReactNode
}

export function SceneLayout({ preset, children }: SceneLayoutProps) {
  const p = PRESETS[preset]

  return (
    <div style={{ minHeight: '100vh', position: 'relative', overflow: 'hidden', background: '#050306' }}>
      {/* Layer 0 — hero photo */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={p.bg}
        alt=""
        style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'cover', zIndex: 0,
          filter: 'saturate(0.88) contrast(1.08)',
        }}
      />

      {/* Layer 1 — dark base overlay */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1,
        background: `rgba(0,0,0,${p.overlay})`,
      }} />

      {/* Layer 2 — accent radial lighting */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 2, pointerEvents: 'none',
        background: `radial-gradient(ellipse ${p.lighting.size} at ${p.lighting.position}, ${p.lighting.color} 0%, rgba(0,0,0,0) 65%)`,
        mixBlendMode: 'screen',
        opacity: p.lighting.intensity,
      }} />

      {/* Layer 3 — demon slayer-style breathing motif */}
      {p.breathing && <BreathingMotif color={p.breathing.color} motif={p.breathing.motif} />}

      {/* Layer 4 — vignette corners */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 4, pointerEvents: 'none',
        background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.75) 100%)',
      }} />

      {/* Layer 5 — paper-noise grain */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 5, pointerEvents: 'none', opacity: 0.08,
        backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.95' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.5 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")`,
        mixBlendMode: 'overlay',
      }} />

      {/* Layer 6 — giant kanji watermark (if present) */}
      {p.kanji && (
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%,-50%)',
          fontSize: '44vw', fontFamily: 'serif',
          color: p.accent,
          opacity: 0.045,
          lineHeight: 1, userSelect: 'none', pointerEvents: 'none', zIndex: 6,
          textShadow: `0 0 80px ${p.accent}`,
        }}>
          {p.kanji}
        </div>
      )}

      {/* Layer 10 — UI content */}
      <div style={{ position: 'relative', zIndex: 10, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {children}
      </div>
    </div>
  )
}

function BreathingMotif({ color, motif }: { color: string; motif: string }) {
  switch (motif) {
    case 'ripples':
      return (
        <svg style={{ position: 'absolute', inset: 0, zIndex: 3, width: '100%', height: '100%', pointerEvents: 'none' }}
             viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice">
          {[0, 1, 2, 3, 4].map((i) => (
            <ellipse key={i}
              cx={300 + i * 220} cy={700 - (i % 2) * 40}
              rx={80 + i * 20} ry={12 + i * 3}
              fill="none" stroke={color} strokeWidth="1.2"
              opacity={0.7 - i * 0.1}
            />
          ))}
          {[0, 1, 2].map((i) => (
            <path key={'w' + i}
              d={`M 0 ${540 + i * 60} Q 350 ${530 + i * 60} 700 ${540 + i * 60} T 1400 ${540 + i * 60}`}
              fill="none" stroke={color} strokeWidth="1" opacity="0.5"
            />
          ))}
        </svg>
      )
    case 'embers':
      return (
        <svg style={{ position: 'absolute', inset: 0, zIndex: 3, width: '100%', height: '100%', pointerEvents: 'none' }}
             viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice">
          {Array.from({ length: 30 }).map((_, i) => {
            const x = (i * 53) % 1400
            const y = (i * 137) % 900
            const r = 1 + (i % 3)
            return <circle key={i} cx={x} cy={y} r={r} fill={color} opacity={0.6 + (i % 4) * 0.1} />
          })}
        </svg>
      )
    case 'petals':
      return (
        <svg style={{ position: 'absolute', inset: 0, zIndex: 3, width: '100%', height: '100%', pointerEvents: 'none' }}
             viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice">
          {Array.from({ length: 22 }).map((_, i) => {
            const x = (i * 73) % 1400
            const y = (i * 43) % 900
            const rot = (i * 37) % 360
            return (
              <g key={i} transform={`translate(${x} ${y}) rotate(${rot})`}>
                <path d="M0 -6 Q4 -3 3 3 Q0 5 -3 3 Q-4 -3 0 -6 Z" fill={color} opacity={0.75} />
              </g>
            )
          })}
        </svg>
      )
    case 'scrolls':
      return (
        <svg style={{ position: 'absolute', inset: 0, zIndex: 3, width: '100%', height: '100%', pointerEvents: 'none' }}
             viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice">
          {[0, 1, 2, 3].map((i) => (
            <path key={i}
              d={`M ${100 + i * 300} 200 Q ${150 + i * 300} ${300 + i * 40} ${180 + i * 300} ${450 + i * 20} T ${220 + i * 300} 720`}
              fill="none" stroke={color} strokeWidth="0.8" opacity="0.55" strokeDasharray="3 6"
            />
          ))}
        </svg>
      )
    case 'mist':
      return (
        <svg style={{ position: 'absolute', inset: 0, zIndex: 3, width: '100%', height: '100%', pointerEvents: 'none' }}
             viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <ellipse key={i}
              cx={200 + i * 220} cy={300 + (i % 2) * 300}
              rx={180} ry={28}
              fill={color} opacity="0.4"
            />
          ))}
        </svg>
      )
    default:
      return null
  }
}
