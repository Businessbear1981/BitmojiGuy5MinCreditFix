'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface ArmorWarriorProps {
  idUploaded: boolean
  addressUploaded: boolean
  reportUploaded: boolean
  swordUnsheathed: boolean
}

const ACCENT = '#C9A84C'

interface PieceConfig {
  key: string
  label: string
  kanji: string
  active: boolean
}

export function ArmorWarrior({ idUploaded, addressUploaded, reportUploaded, swordUnsheathed }: ArmorWarriorProps) {
  const allArmored = idUploaded && addressUploaded && reportUploaded
  const armoredCount = [idUploaded, addressUploaded, reportUploaded].filter(Boolean).length
  const [flash, setFlash] = useState(false)
  const [shake, setShake] = useState(false)
  const prevCount = useRef(armoredCount)

  const pieces: PieceConfig[] = [
    { key: 'helm',   label: 'Helm',        kanji: '面', active: idUploaded },
    { key: 'chest',  label: 'Breastplate', kanji: '鎧', active: addressUploaded },
    { key: 'sword',  label: 'Sword',       kanji: '剣', active: reportUploaded },
  ]

  useEffect(() => {
    if (armoredCount === prevCount.current) return
    if (armoredCount > prevCount.current) {
      setFlash(true)
      setShake(true)
      const t1 = setTimeout(() => setFlash(false), 1200)
      const t2 = setTimeout(() => setShake(false), 600)
      prevCount.current = armoredCount
      return () => { clearTimeout(t1); clearTimeout(t2) }
    }
    prevCount.current = armoredCount
  }, [armoredCount])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
      <div style={{
        position: 'relative',
        width: 220,
        height: 352,
        animation: shake ? 'forgeShake 0.6s ease' : undefined,
      }}>
        {/* Gold aura */}
        <div style={{
          position: 'absolute',
          top: '45%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: armoredCount === 0 ? 0 : 140 + armoredCount * 40,
          height: armoredCount === 0 ? 0 : 140 + armoredCount * 40,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${ACCENT}${armoredCount === 3 ? '35' : '18'} 0%, transparent 70%)`,
          transition: 'all 1.2s ease',
          pointerEvents: 'none',
        }} />

        {/* BASE: Bitmoji in white (no armor) — always visible underneath */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/bitmoji-base.png"
          alt="BitmojiGuy & Maverick"
          style={{
            width: 220,
            height: 352,
            objectFit: 'contain',
            display: 'block',
            position: 'absolute',
            top: 0,
            left: 0,
            zIndex: 1,
          }}
        />

        {/* ARMOR PIECE 1: Helmet region — revealed on ID upload (top 30%) */}
        <AnimatePresence>
          {idUploaded && (
            <motion.div
              key="helmet"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 120, damping: 12 }}
              style={{
                position: 'absolute', top: 0, left: 0, width: 220, height: 352,
                zIndex: 2, clipPath: 'polygon(20% 0%, 80% 0%, 80% 28%, 20% 28%)',
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/bitmoji-warrior.png" alt="" style={{ width: 220, height: 352, objectFit: 'contain' }} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* ARMOR PIECE 2: Breastplate region — revealed on address upload (middle 30-65%) */}
        <AnimatePresence>
          {addressUploaded && (
            <motion.div
              key="chest"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: 'spring', stiffness: 130, damping: 13 }}
              style={{
                position: 'absolute', top: 0, left: 0, width: 220, height: 352,
                zIndex: 2, clipPath: 'polygon(10% 28%, 90% 28%, 90% 62%, 10% 62%)',
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/bitmoji-warrior.png" alt="" style={{ width: 220, height: 352, objectFit: 'contain' }} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* ARMOR PIECE 3: Legs + sword region — revealed on report upload (bottom 62-100%) */}
        <AnimatePresence>
          {reportUploaded && (
            <motion.div
              key="legs"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 100, damping: 12 }}
              style={{
                position: 'absolute', top: 0, left: 0, width: 220, height: 352,
                zIndex: 2, clipPath: 'polygon(5% 62%, 95% 62%, 95% 100%, 5% 100%)',
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/bitmoji-warrior.png" alt="" style={{ width: 220, height: 352, objectFit: 'contain' }} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* FULL WARRIOR — shown when all 3 uploaded, replaces the clipped pieces */}
        {allArmored && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
            style={{ position: 'absolute', top: 0, left: 0, zIndex: 3 }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/bitmoji-warrior.png" alt="BitmojiGuy Fully Armored" style={{ width: 220, height: 352, objectFit: 'contain' }} />
          </motion.div>
        )}

        {/* Forge flash */}
        {flash && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 5, borderRadius: 12,
            background: `radial-gradient(circle at 50% 40%, ${ACCENT}88 0%, transparent 55%)`,
            animation: 'forgeFlash 1.2s ease-out forwards', pointerEvents: 'none',
          }} />
        )}

        {/* Gold glow ring when fully armored */}
        {swordUnsheathed && (
          <div style={{
            position: 'absolute', inset: -8, zIndex: 3, borderRadius: 12,
            border: `2px solid ${ACCENT}`,
            boxShadow: `0 0 24px ${ACCENT}88, 0 0 48px ${ACCENT}44, inset 0 0 24px ${ACCENT}22`,
            animation: 'armorGlowAnim 2.5s ease-in-out infinite', pointerEvents: 'none',
          }} />
        )}

        {/* Armor count */}
        <div style={{
          position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)', zIndex: 4,
          fontFamily: 'var(--font-cinzel-decorative), serif',
          fontSize: allArmored ? 14 : 12, letterSpacing: 3, textTransform: 'uppercase',
          color: allArmored ? ACCENT : '#8A8278',
          textShadow: allArmored ? `0 0 8px ${ACCENT}, 0 0 20px ${ACCENT}88` : '0 0 8px rgba(0,0,0,0.8)',
          whiteSpace: 'nowrap', transition: 'all 0.6s',
        }}>
          {allArmored ? '\u2694 ARMED' : `${armoredCount} / 3`}
        </div>
      </div>

      {/* Armor piece indicators */}
      <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
        {pieces.map((p) => (
          <div key={p.key} style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
            padding: '10px 14px', borderRadius: 6, minWidth: 62,
            border: `1px solid ${p.active ? ACCENT + '88' : 'rgba(138,130,120,0.15)'}`,
            background: p.active ? `linear-gradient(135deg, ${ACCENT}22, ${ACCENT}08)` : 'rgba(0,0,0,0.3)',
            boxShadow: p.active ? `0 0 16px ${ACCENT}44, inset 0 0 8px ${ACCENT}11` : 'none',
            transition: 'all 0.6s ease',
          }}>
            <span style={{
              fontFamily: 'serif', fontSize: 22, color: p.active ? ACCENT : '#5A5A5A',
              lineHeight: 1, transition: 'color 0.4s',
              textShadow: p.active ? `0 0 8px ${ACCENT}88, 0 0 16px ${ACCENT}44` : 'none',
            }}>
              {p.active ? '\u2713' : p.kanji}
            </span>
            <span style={{
              fontFamily: 'var(--font-cinzel), serif', fontSize: 8, letterSpacing: 1.5,
              textTransform: 'uppercase', color: p.active ? ACCENT : '#8A8278', transition: 'color 0.4s',
            }}>
              {p.label}
            </span>
            <div style={{
              width: 4, height: 4, borderRadius: '50%',
              background: p.active ? ACCENT : '#3A3A3A',
              boxShadow: p.active ? `0 0 6px ${ACCENT}` : 'none', transition: 'all 0.4s',
            }} />
          </div>
        ))}
      </div>

      <style>{`
        @keyframes armorGlowAnim {
          0%, 100% { box-shadow: 0 0 24px ${ACCENT}88, 0 0 48px ${ACCENT}44, inset 0 0 24px ${ACCENT}22; }
          50%      { box-shadow: 0 0 36px ${ACCENT}CC, 0 0 72px ${ACCENT}66, inset 0 0 36px ${ACCENT}33; }
        }
        @keyframes forgeFlash {
          0%   { opacity: 1; transform: scale(1); }
          50%  { opacity: 0.7; transform: scale(1.05); }
          100% { opacity: 0; transform: scale(1.1); }
        }
        @keyframes forgeShake {
          0%, 100% { transform: translateX(0); }
          15% { transform: translateX(-5px) rotate(-1.5deg); }
          30% { transform: translateX(5px) rotate(1.5deg); }
          45% { transform: translateX(-3px) rotate(-0.5deg); }
          60% { transform: translateX(3px) rotate(0.5deg); }
          75% { transform: translateX(-1px); }
        }
      `}</style>
    </div>
  )
}
