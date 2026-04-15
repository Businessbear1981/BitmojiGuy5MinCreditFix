'use client'

import { motion } from 'framer-motion'

const EASE = [0.77, 0, 0.175, 1] as const
const DURATION = 1.1

const gridBg = `
  repeating-linear-gradient(0deg, rgba(201,168,76,0.07) 0, rgba(201,168,76,0.07) 1px, transparent 1px, transparent 55px),
  repeating-linear-gradient(90deg, rgba(201,168,76,0.07) 0, rgba(201,168,76,0.07) 1px, transparent 1px, transparent 38px)
`

export function ShojiDoors({ isOpen }: { isOpen: boolean }) {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        pointerEvents: isOpen ? 'none' : 'all',
      }}
    >
      {/* Top rail */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 14, background: 'rgba(80,50,10,0.92)', borderBottom: '1px solid rgba(201,168,76,0.4)', zIndex: 51 }} />
      {/* Bottom rail */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 10, background: 'rgba(80,50,10,0.88)', borderTop: '1px solid rgba(201,168,76,0.3)', zIndex: 51 }} />

      {/* Left door */}
      <motion.div
        animate={{ x: isOpen ? '-100%' : 0 }}
        transition={{ duration: DURATION, ease: EASE }}
        style={{
          width: '50%',
          height: '100%',
          position: 'relative',
          overflow: 'hidden',
          transformOrigin: 'left center',
          borderRight: '2px solid rgba(201,168,76,0.35)',
          background: 'rgba(10,8,6,0.88)',
          backgroundImage: gridBg,
        }}
      >
        {/* Wood frame strip */}
        <div style={{ position: 'absolute', top: 0, right: 0, width: 10, height: '100%', background: 'rgba(100,65,15,0.55)', borderLeft: '1px solid rgba(201,168,76,0.3)' }} />
        {/* Pull handle */}
        <div style={{ position: 'absolute', top: '50%', right: 16, transform: 'translateY(-50%)', width: 5, height: 70, background: 'rgba(201,168,76,0.45)', borderRadius: 3 }} />
      </motion.div>

      {/* Right door */}
      <motion.div
        animate={{ x: isOpen ? '100%' : 0 }}
        transition={{ duration: DURATION, ease: EASE }}
        style={{
          width: '50%',
          height: '100%',
          position: 'relative',
          overflow: 'hidden',
          transformOrigin: 'right center',
          borderLeft: '2px solid rgba(201,168,76,0.35)',
          background: 'rgba(10,8,6,0.88)',
          backgroundImage: gridBg,
        }}
      >
        {/* Wood frame strip */}
        <div style={{ position: 'absolute', top: 0, left: 0, width: 10, height: '100%', background: 'rgba(100,65,15,0.55)', borderRight: '1px solid rgba(201,168,76,0.3)' }} />
        {/* Pull handle */}
        <div style={{ position: 'absolute', top: '50%', left: 16, transform: 'translateY(-50%)', width: 5, height: 70, background: 'rgba(201,168,76,0.45)', borderRadius: 3 }} />
      </motion.div>
    </div>
  )
}
