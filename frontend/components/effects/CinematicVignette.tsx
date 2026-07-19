'use client'

import { motion } from 'framer-motion'

interface CinematicVignetteProps {
  intensity?: number
  color?: string
  animated?: boolean
}

export function CinematicVignette({ intensity = 0.6, color = 'rgba(0,0,0,0.7)', animated = true }: CinematicVignetteProps) {
  return (
    <motion.div
      animate={
        animated
          ? {
              boxShadow: [
                `inset 0 0 60px ${color}`,
                `inset 0 0 80px ${color}`,
                `inset 0 0 60px ${color}`,
              ],
            }
          : {}
      }
      transition={animated ? { duration: 6, repeat: Infinity, ease: 'easeInOut' } : {}}
      style={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 9,
        boxShadow: `inset 0 0 60px ${color}`,
      }}
    />
  )
}
