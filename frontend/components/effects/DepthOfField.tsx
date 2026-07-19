'use client'

import { ReactNode } from 'react'

interface DepthOfFieldProps {
  children: ReactNode
  foregroundBlur?: number
  backgroundBlur?: number
  focusIntensity?: number
}

export function DepthOfField({
  children,
  foregroundBlur = 0,
  backgroundBlur = 8,
  focusIntensity = 1,
}: DepthOfFieldProps) {
  return (
    <div
      style={{
        position: 'relative',
        filter: `blur(${foregroundBlur}px)`,
        opacity: focusIntensity,
        transition: 'all 0.3s ease',
      }}
    >
      {children}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 0%, rgba(0,0,0,0.3) 100%)',
          pointerEvents: 'none',
        }}
      />
    </div>
  )
}
