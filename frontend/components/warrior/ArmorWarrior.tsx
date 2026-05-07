'use client'

import { motion } from 'framer-motion'

interface ArmorWarriorProps {
  idUploaded: boolean
  addressUploaded: boolean
  reportUploaded: boolean
  swordUnsheathed: boolean
  pieces?: string[]
}

const armorAppear = (visible: boolean): React.CSSProperties => ({
  opacity: visible ? 1 : 0,
  transform: visible ? 'scale(1) translateY(0)' : 'scale(0.85) translateY(20px)',
  transition: 'opacity 0.7s cubic-bezier(0.34, 1.56, 0.64, 1), transform 0.7s cubic-bezier(0.34, 1.56, 0.64, 1)',
  transformOrigin: 'center center',
})

export function ArmorWarrior({ idUploaded, addressUploaded, reportUploaded, swordUnsheathed, pieces = [] }: ArmorWarriorProps) {
  // Calculate total armor count for stance progression
  const armorCount = [idUploaded, addressUploaded, reportUploaded].filter(Boolean).length

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, ease: 'easeOut' }}
      style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-end' }}
    >
      <svg width="240" height="420" viewBox="0 0 240 420" style={{ filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.4))' }}>
        {/* ─── BACKGROUND AURA ─── */}
        <defs>
          <radialGradient id="auraGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(201,168,76,0.3)" />
            <stop offset="100%" stopColor="rgba(201,168,76,0)" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <linearGradient id="metalGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#E8D4B8" />
            <stop offset="50%" stopColor="#C9A84C" />
            <stop offset="100%" stopColor="#8B6914" />
          </linearGradient>
          <linearGradient id="steelGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#4A4A4A" />
            <stop offset="50%" stopColor="#2A2A2A" />
            <stop offset="100%" stopColor="#1A1A1A" />
          </linearGradient>
        </defs>

        {/* Aura circle behind warrior */}
        <motion.circle
          cx="120"
          cy="200"
          r="110"
          fill="url(#auraGradient)"
          animate={{
            r: armorCount > 0 ? 115 : 100,
            opacity: armorCount > 0 ? 0.6 : 0.3,
          }}
          transition={{ duration: 0.6 }}
        />

        {/* ─── BASE FIGURE (always visible) ─── */}
        {/* Head */}
        <ellipse cx="120" cy="60" rx="22" ry="26" fill="#1A1610" stroke="#0A0806" strokeWidth="2" />
        {/* Face details */}
        <circle cx="115" cy="56" r="2.5" fill="#8A7860" />
        <circle cx="125" cy="56" r="2.5" fill="#8A7860" />
        <line x1="115" y1="65" x2="125" y2="65" stroke="#8A7860" strokeWidth="1" />

        {/* Neck */}
        <rect x="112" y="84" width="16" height="12" fill="#1A1610" stroke="#0A0806" strokeWidth="1" />

        {/* Underrobe body */}
        <path
          d="M 85 94 L 85 160 Q 85 168 92 170 L 148 170 Q 155 168 155 160 L 155 94 Q 155 90 150 90 L 90 90 Q 85 90 85 94 Z"
          fill="#E8E0D0"
          opacity="0.12"
          stroke="#2A2418"
          strokeWidth="2"
        />

        {/* Kimono collar V-lines */}
        <line x1="100" y1="94" x2="120" y2="118" stroke="#2A2418" strokeWidth="2" opacity="0.6" />
        <line x1="140" y1="94" x2="120" y2="118" stroke="#2A2418" strokeWidth="2" opacity="0.6" />

        {/* Arms — dynamic based on armor count */}
        {armorCount < 3 ? (
          <>
            {/* Left arm relaxed */}
            <rect x="70" y="100" width="18" height="62" rx="6" fill="#1A1610" stroke="#0A0806" strokeWidth="2" />
            <ellipse cx="79" cy="166" rx="7" ry="6" fill="#1A1610" stroke="#0A0806" strokeWidth="1.5" />

            {/* Right arm relaxed */}
            <rect x="152" y="100" width="18" height="62" rx="6" fill="#1A1610" stroke="#0A0806" strokeWidth="2" />
            <ellipse cx="161" cy="166" rx="7" ry="6" fill="#1A1610" stroke="#0A0806" strokeWidth="1.5" />
          </>
        ) : (
          <>
            {/* Left arm ready */}
            <rect x="70" y="100" width="18" height="62" rx="6" fill="#1A1610" stroke="#0A0806" strokeWidth="2" />
            <ellipse cx="79" cy="166" rx="7" ry="6" fill="#1A1610" stroke="#0A0806" strokeWidth="1.5" />

            {/* Right arm raised for sword grip */}
            <motion.g
              animate={{ y: -8, rotate: -15 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              style={{ transformOrigin: '161 100' }}
            >
              <rect x="152" y="100" width="18" height="58" rx="6" fill="#1A1610" stroke="#0A0806" strokeWidth="2" />
              <ellipse cx="161" cy="158" rx="7" ry="6" fill="#1A1610" stroke="#0A0806" strokeWidth="1.5" />
            </motion.g>
          </>
        )}

        {/* Hakama pants */}
        <path
          d="M 90 168 L 90 260 Q 90 268 96 270 L 144 270 Q 150 268 150 260 L 150 168 Z"
          fill="#0E0C08"
          stroke="#0A0806"
          strokeWidth="2"
        />

        {/* Pleat lines */}
        <line x1="105" y1="168" x2="105" y2="270" stroke="#1A1610" strokeWidth="0.5" opacity="0.4" />
        <line x1="120" y1="168" x2="120" y2="270" stroke="#1A1610" strokeWidth="0.5" opacity="0.4" />
        <line x1="135" y1="168" x2="135" y2="270" stroke="#1A1610" strokeWidth="0.5" opacity="0.4" />

        {/* Tabi feet */}
        <ellipse cx="105" cy="280" rx="11" ry="6" fill="#E8E0D0" opacity="0.14" stroke="#1A1610" strokeWidth="1.5" />
        <ellipse cx="135" cy="280" rx="11" ry="6" fill="#E8E0D0" opacity="0.14" stroke="#1A1610" strokeWidth="1.5" />

        {/* ─── ARMOR LAYER 1: DO (Chest Plate) — on ID upload ─── */}
        <motion.g
          style={armorAppear(idUploaded)}
          animate={{ filter: idUploaded ? 'drop-shadow(0 8px 16px rgba(201,168,76,0.4))' : 'drop-shadow(0 0 0 rgba(201,168,76,0))' }}
        >
          {/* Main chest plate */}
          <path
            d="M 85 100 L 85 160 Q 85 168 92 170 L 148 170 Q 155 168 155 160 L 155 100 Z"
            fill="url(#metalGradient)"
            stroke="#8B6914"
            strokeWidth="2.5"
          />

          {/* Lamellar horizontal lines */}
          <line x1="88" y1="112" x2="152" y2="112" stroke="#C9A84C" opacity="0.4" strokeWidth="0.8" />
          <line x1="88" y1="125" x2="152" y2="125" stroke="#C9A84C" opacity="0.35" strokeWidth="0.8" />
          <line x1="88" y1="138" x2="152" y2="138" stroke="#C9A84C" opacity="0.3" strokeWidth="0.8" />
          <line x1="88" y1="151" x2="152" y2="151" stroke="#C9A84C" opacity="0.25" strokeWidth="0.8" />

          {/* Mon crest center */}
          <circle cx="120" cy="135" r="12" fill="none" stroke="#C9A84C" strokeWidth="2" opacity="0.6" />
          <circle cx="120" cy="135" r="8" fill="none" stroke="#C9A84C" strokeWidth="1" opacity="0.4" />

          {/* Shoulder pauldrons left */}
          <ellipse cx="75" cy="105" rx="10" ry="14" fill="url(#metalGradient)" stroke="#8B6914" strokeWidth="2" />
          {/* Shoulder pauldrons right */}
          <ellipse cx="165" cy="105" rx="10" ry="14" fill="url(#metalGradient)" stroke="#8B6914" strokeWidth="2" />
        </motion.g>

        {/* ─── ARMOR LAYER 2: KABUTO (Helmet) — on Address upload ─── */}
        <motion.g style={armorAppear(addressUploaded)}>
          {/* Helmet bowl */}
          <ellipse cx="120" cy="48" rx="28" ry="24" fill="url(#steelGradient)" stroke="#8B6914" strokeWidth="2.5" />

          {/* Helmet shine/highlight */}
          <ellipse cx="115" cy="42" rx="12" ry="8" fill="#E8D4B8" opacity="0.3" />

          {/* Maedate horns */}
          <path d="M 95 32 Q 90 18 100 12" fill="none" stroke="#C9A84C" strokeWidth="3" strokeLinecap="round" />
          <path d="M 145 32 Q 150 18 140 12" fill="none" stroke="#C9A84C" strokeWidth="3" strokeLinecap="round" />

          {/* Fukigaeshi side guards left */}
          <path d="M 88 52 L 78 66 L 88 68 Z" fill="#2A2A2A" stroke="#8B6914" strokeWidth="1.5" />
          {/* Fukigaeshi side guards right */}
          <path d="M 152 52 L 162 66 L 152 68 Z" fill="#2A2A2A" stroke="#8B6914" strokeWidth="1.5" />

          {/* Shikoro neck plates */}
          <path d="M 88 68 L 82 82 L 120 92 L 158 82 L 152 68 Z" fill="#2A2A2A" stroke="#8B6914" strokeWidth="2" />
          <path d="M 88 75 L 120 85 L 152 75" fill="none" stroke="#C9A84C" opacity="0.3" strokeWidth="0.5" />
        </motion.g>

        {/* ─── ARMOR LAYER 3: KOTE (Arm & Shoulder Guards) — on Report upload ─── */}
        <motion.g style={armorAppear(reportUploaded)}>
          {/* Left shoulder guard */}
          <rect x="62" y="92" width="26" height="32" rx="3" fill="url(#steelGradient)" stroke="#8B6914" strokeWidth="2" />
          <line x1="66" y1="104" x2="84" y2="104" stroke="#C9A84C" opacity="0.3" strokeWidth="0.6" />
          <line x1="66" y1="114" x2="84" y2="114" stroke="#C9A84C" opacity="0.3" strokeWidth="0.6" />

          {/* Left arm guard */}
          <rect x="62" y="126" width="24" height="44" rx="3" fill="url(#steelGradient)" stroke="#8B6914" strokeWidth="2" />
          <line x1="66" y1="140" x2="82" y2="140" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
          <line x1="66" y1="155" x2="82" y2="155" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />

          {/* Right shoulder guard */}
          <rect x="152" y="92" width="26" height="32" rx="3" fill="url(#steelGradient)" stroke="#8B6914" strokeWidth="2" />
          <line x1="156" y1="104" x2="174" y2="104" stroke="#C9A84C" opacity="0.3" strokeWidth="0.6" />
          <line x1="156" y1="114" x2="174" y2="114" stroke="#C9A84C" opacity="0.3" strokeWidth="0.6" />

          {/* Right arm guard */}
          <rect x="154" y="126" width="24" height="44" rx="3" fill="url(#steelGradient)" stroke="#8B6914" strokeWidth="2" />
          <line x1="158" y1="140" x2="174" y2="140" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
          <line x1="158" y1="155" x2="174" y2="155" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
        </motion.g>

        {/* ─── ARMOR LAYER 4: KUSAZURI (Leg Plates) — always visible when other armor present ─── */}
        <motion.g style={armorAppear(addressUploaded || reportUploaded)}>
          {/* Left leg guard */}
          <rect x="82" y="170" width="28" height="88" rx="2" fill="url(#steelGradient)" stroke="#8B6914" strokeWidth="2" />
          <line x1="86" y1="188" x2="106" y2="188" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
          <line x1="86" y1="208" x2="106" y2="208" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
          <line x1="86" y1="228" x2="106" y2="228" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
          <line x1="86" y1="248" x2="106" y2="248" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />

          {/* Right leg guard */}
          <rect x="130" y="170" width="28" height="88" rx="2" fill="url(#steelGradient)" stroke="#8B6914" strokeWidth="2" />
          <line x1="134" y1="188" x2="154" y2="188" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
          <line x1="134" y1="208" x2="154" y2="208" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
          <line x1="134" y1="228" x2="154" y2="228" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
          <line x1="134" y1="248" x2="154" y2="248" stroke="#C9A84C" opacity="0.25" strokeWidth="0.6" />
        </motion.g>

        {/* ─── ARMOR LAYER 5: KATANA (Sword) — on all armor complete ─── */}
        <motion.g
          style={armorAppear(swordUnsheathed)}
          animate={{
            x: swordUnsheathed ? 0 : 20,
            y: swordUnsheathed ? 0 : 40,
            rotate: swordUnsheathed ? 0 : 45,
          }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        >
          {/* Blade — layered for depth */}
          <line x1="168" y1="190" x2="185" y2="10" stroke="#1A1A1A" strokeWidth="5" strokeLinecap="round" />
          <line x1="169" y1="190" x2="186" y2="10" stroke="#4A4A4A" strokeWidth="2.5" strokeLinecap="round" />
          <line x1="170" y1="188" x2="187" y2="12" stroke="#E8D4B8" strokeWidth="1.2" strokeLinecap="round" opacity="0.6" />

          {/* Tsuba guard */}
          <ellipse cx="165" cy="185" rx="10" ry="6" fill="#2A2A2A" stroke="#C9A84C" strokeWidth="2.5" />
          <circle cx="165" cy="185" r="5" fill="none" stroke="#C9A84C" strokeWidth="1" opacity="0.5" />

          {/* Handle — wrapped */}
          <rect x="160" y="188" width="10" height="36" rx="3" fill="#2A2A2A" stroke="#8B6914" strokeWidth="1.5" />
          <line x1="162" y1="188" x2="162" y2="224" stroke="#C9A84C" strokeWidth="1" opacity="0.4" strokeDasharray="3 2" />
          <line x1="168" y1="188" x2="168" y2="224" stroke="#C9A84C" strokeWidth="1" opacity="0.4" strokeDasharray="3 2" />

          {/* Pommel */}
          <circle cx="165" cy="230" r="5" fill="#2A2A2A" stroke="#8B6914" strokeWidth="1.5" />
          <circle cx="165" cy="230" r="3" fill="#C9A84C" opacity="0.6" />

          {/* Sword glow */}
          <motion.line
            x1="168"
            y1="190"
            x2="185"
            y2="10"
            stroke="#C9A84C"
            strokeWidth="2"
            opacity="0"
            animate={{ opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 2, repeat: Infinity }}
            filter="url(#glow)"
          />
        </motion.g>

        {/* ─── PARTICLE EFFECTS (Sparks on armor completion) ─── */}
        {idUploaded && (
          <motion.g
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            {[0, 1, 2, 3].map((i) => (
              <motion.circle
                key={`spark-id-${i}`}
                cx={85 + Math.random() * 70}
                cy={100 + Math.random() * 80}
                r="1.5"
                fill="#C9A84C"
                animate={{
                  y: [0, -40],
                  opacity: [1, 0],
                }}
                transition={{ duration: 0.8, delay: i * 0.1 }}
              />
            ))}
          </motion.g>
        )}

        {addressUploaded && (
          <motion.g
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            {[0, 1, 2, 3].map((i) => (
              <motion.circle
                key={`spark-addr-${i}`}
                cx={100 + Math.random() * 40}
                cy={50 + Math.random() * 60}
                r="1.5"
                fill="#C9A84C"
                animate={{
                  y: [0, -40],
                  opacity: [1, 0],
                }}
                transition={{ duration: 0.8, delay: i * 0.1 }}
              />
            ))}
          </motion.g>
        )}

        {reportUploaded && (
          <motion.g
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            {[0, 1, 2, 3].map((i) => (
              <motion.circle
                key={`spark-report-${i}`}
                cx={110 + Math.random() * 50}
                cy={80 + Math.random() * 70}
                r="1.5"
                fill="#C9A84C"
                animate={{
                  y: [0, -40],
                  opacity: [1, 0],
                }}
                transition={{ duration: 0.8, delay: i * 0.1 }}
              />
            ))}
          </motion.g>
        )}
      </svg>
    </motion.div>
  )
}
