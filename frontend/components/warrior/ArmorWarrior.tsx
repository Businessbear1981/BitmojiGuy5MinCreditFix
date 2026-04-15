'use client'

interface ArmorWarriorProps {
  idUploaded: boolean
  addressUploaded: boolean
  reportUploaded: boolean
  swordUnsheathed: boolean
  pieces?: string[]
}

const armorAppear = (visible: boolean): React.CSSProperties => ({
  opacity: visible ? 1 : 0,
  transform: visible ? 'scale(1)' : 'scale(1.08)',
  transition: 'opacity 0.8s ease, transform 0.3s ease',
  transformOrigin: 'center center',
})

export function ArmorWarrior({ idUploaded, addressUploaded, reportUploaded, swordUnsheathed, pieces = [] }: ArmorWarriorProps) {
  return (
    <svg width="200" height="380" viewBox="0 0 200 380">
      {/* ─── BASE FIGURE (always visible) ─── */}
      {/* Head — heavy outline */}
      <ellipse cx="100" cy="52" rx="20" ry="24" fill="#1A1610" stroke="#0A0806" strokeWidth="2.5" />
      {/* Neck */}
      <rect x="93" y="74" width="14" height="10" fill="#1A1610" />
      {/* White underrobe body — heavy outline */}
      <rect x="72" y="82" width="56" height="90" rx="3" fill="#E8E0D0" opacity="0.15" stroke="#1A1610" strokeWidth="2.5" />
      {/* Kimono collar V lines — medium weight */}
      <line x1="86" y1="82" x2="100" y2="104" stroke="#2A2418" strokeWidth="2" />
      <line x1="114" y1="82" x2="100" y2="104" stroke="#2A2418" strokeWidth="2" />
      {/* Left arm — heavy outline */}
      <rect x="56" y="88" width="18" height="54" rx="5" fill="#1A1610" stroke="#0A0806" strokeWidth="2.5" />
      <ellipse cx="65" cy="146" rx="6" ry="5.5" fill="#1A1610" stroke="#0A0806" strokeWidth="2" />
      {/* Right arm — heavy outline */}
      <rect x="126" y="88" width="18" height="54" rx="5" fill="#1A1610" stroke="#0A0806" strokeWidth="2.5" />
      <ellipse cx="135" cy="146" rx="6" ry="5.5" fill="#1A1610" stroke="#0A0806" strokeWidth="2" />
      {/* Hakama pants — heavy outline */}
      <rect x="74" y="170" width="52" height="90" rx="2" fill="#0E0C08" stroke="#0A0806" strokeWidth="2.5" />
      {/* Pleat lines — thin detail */}
      <line x1="88" y1="170" x2="88" y2="260" stroke="#1A1610" strokeWidth="0.5" />
      <line x1="100" y1="170" x2="100" y2="260" stroke="#1A1610" strokeWidth="0.5" />
      <line x1="112" y1="170" x2="112" y2="260" stroke="#1A1610" strokeWidth="0.5" />
      {/* Tabi sock feet — medium outline */}
      <ellipse cx="88" cy="266" rx="10" ry="5" fill="#E8E0D0" opacity="0.12" stroke="#1A1610" strokeWidth="1.5" />
      <ellipse cx="112" cy="266" rx="10" ry="5" fill="#E8E0D0" opacity="0.12" stroke="#1A1610" strokeWidth="1.5" />

      {/* ─── ARMOR BREASTPLATE (pieces-based) ─── */}
      <g id="armor-breastplate" style={armorAppear(pieces.includes('breastplate'))}>
        {/* Heavy outer border */}
        <rect x="52" y="72" width="96" height="88" fill="#1E1C12" stroke="#C9A84C" strokeWidth="2.5" />
        {/* Thin lamellar detail lines */}
        <line x1="56" y1="80" x2="144" y2="80" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="56" y1="90" x2="144" y2="90" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="56" y1="100" x2="144" y2="100" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="56" y1="110" x2="144" y2="110" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="56" y1="120" x2="144" y2="120" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="56" y1="130" x2="144" y2="130" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="56" y1="140" x2="144" y2="140" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="56" y1="148" x2="144" y2="148" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        {/* Mon crest — medium stroke */}
        <circle cx="100" cy="108" r="10" fill="none" stroke="#C9A84C" opacity="0.4" strokeWidth="1.5" />
      </g>

      {/* ─── ARMOR HELMET (pieces-based) ─── */}
      <g id="armor-helmet" style={armorAppear(pieces.includes('helmet'))}>
        {/* Kabuto bowl — heavy outline */}
        <ellipse cx="100" cy="32" rx="26" ry="22" fill="#1E1C12" stroke="#C9A84C" strokeWidth="2.5" />
        {/* Maedate crescent — heavy */}
        <path d="M82 18 Q100 -2 118 18" fill="#C9A84C" opacity="0.75" stroke="#C9A84C" strokeWidth="2" />
        {/* Left fukigaeshi — medium */}
        <path d="M74 38 L66 48 L74 50" fill="#1E1C12" stroke="#C9A84C" strokeWidth="1.5" opacity="0.6" />
        {/* Right fukigaeshi — medium */}
        <path d="M126 38 L134 48 L126 50" fill="#1E1C12" stroke="#C9A84C" strokeWidth="1.5" opacity="0.6" />
        {/* Shikoro neck plate 1 — medium outline, thin inner detail */}
        <path d="M72 50 L68 62 L100 70 L132 62 L128 50" fill="#181210" stroke="#C9A84C" strokeWidth="1.5" opacity="0.7" />
        <path d="M72 56 L100 62 L128 56" fill="none" stroke="#C9A84C" strokeWidth="0.5" opacity="0.3" />
        {/* Shikoro neck plate 2 */}
        <path d="M70 62 L66 72 L100 80 L134 72 L130 62" fill="#181210" stroke="#C9A84C" strokeWidth="1" opacity="0.5" />
        <path d="M70 67 L100 74 L130 67" fill="none" stroke="#C9A84C" strokeWidth="0.5" opacity="0.2" />
      </g>

      {/* ─── ARMOR LEGS (pieces-based) ─── */}
      <g id="armor-legs" style={armorAppear(pieces.includes('legs'))}>
        {/* Left leg guard — heavy outline */}
        <rect x="50" y="160" width="40" height="75" fill="#1E1C12" stroke="#C9A84C" strokeWidth="2.5" />
        {/* Thin lamellar details */}
        <line x1="54" y1="176" x2="86" y2="176" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="54" y1="192" x2="86" y2="192" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="54" y1="208" x2="86" y2="208" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="54" y1="224" x2="86" y2="224" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        {/* Right leg guard — heavy outline */}
        <rect x="110" y="160" width="40" height="75" fill="#1E1C12" stroke="#C9A84C" strokeWidth="2.5" />
        <line x1="114" y1="176" x2="146" y2="176" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="114" y1="192" x2="146" y2="192" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="114" y1="208" x2="146" y2="208" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
        <line x1="114" y1="224" x2="146" y2="224" stroke="#C9A84C" opacity="0.25" strokeWidth="0.5" />
      </g>

      {/* ─── ARMOR DO — chest plate (on ID upload) ─── */}
      <g id="armor-do" style={armorAppear(idUploaded)}>
        <rect x="74" y="84" width="52" height="84" rx="2" fill="#1E1810" stroke="rgba(201,168,76,0.5)" strokeWidth="2.5" />
        <line x1="77" y1="96" x2="123" y2="96" stroke="rgba(201,168,76,0.25)" strokeWidth="0.5" />
        <line x1="77" y1="108" x2="123" y2="108" stroke="rgba(201,168,76,0.2)" strokeWidth="0.5" />
        <line x1="77" y1="120" x2="123" y2="120" stroke="rgba(201,168,76,0.18)" strokeWidth="0.5" />
        <line x1="77" y1="132" x2="123" y2="132" stroke="rgba(201,168,76,0.15)" strokeWidth="0.5" />
        <line x1="77" y1="144" x2="123" y2="144" stroke="rgba(201,168,76,0.12)" strokeWidth="0.5" />
        <circle cx="100" cy="122" r="9" fill="none" stroke="rgba(201,168,76,0.4)" strokeWidth="1.5" />
        <circle cx="100" cy="122" r="4" fill="rgba(201,168,76,0.15)" />
        <line x1="76" y1="84" x2="64" y2="74" stroke="rgba(201,168,76,0.3)" strokeWidth="2" />
        <line x1="124" y1="84" x2="136" y2="74" stroke="rgba(201,168,76,0.3)" strokeWidth="2" />
      </g>

      {/* ─── ARMOR KOTE — arm + shoulder guards (on address upload) ─── */}
      <g id="armor-kote" style={armorAppear(addressUploaded)}>
        <rect x="50" y="80" width="22" height="26" rx="2" fill="#1E1810" stroke="rgba(201,168,76,0.4)" strokeWidth="2" />
        <line x1="52" y1="90" x2="70" y2="90" stroke="rgba(201,168,76,0.15)" strokeWidth="0.5" />
        <rect x="52" y="108" width="20" height="36" rx="3" fill="#1E1810" stroke="rgba(201,168,76,0.3)" strokeWidth="2" />
        <line x1="54" y1="120" x2="70" y2="120" stroke="rgba(201,168,76,0.1)" strokeWidth="0.5" />
        <rect x="128" y="80" width="22" height="26" rx="2" fill="#1E1810" stroke="rgba(201,168,76,0.4)" strokeWidth="2" />
        <line x1="130" y1="90" x2="148" y2="90" stroke="rgba(201,168,76,0.15)" strokeWidth="0.5" />
        <rect x="128" y="108" width="20" height="36" rx="3" fill="#1E1810" stroke="rgba(201,168,76,0.3)" strokeWidth="2" />
        <line x1="130" y1="120" x2="146" y2="120" stroke="rgba(201,168,76,0.1)" strokeWidth="0.5" />
      </g>

      {/* ─── ARMOR KABUTO — helmet (on report upload) ─── */}
      <g id="armor-kabuto" style={armorAppear(reportUploaded)}>
        <ellipse cx="100" cy="44" rx="28" ry="20" fill="#1A1208" stroke="#C9A84C" strokeWidth="2.5" />
        <ellipse cx="100" cy="40" rx="22" ry="15" fill="#242018" />
        <path d="M78 42 Q100 28 122 42" fill="none" stroke="rgba(201,168,76,0.2)" strokeWidth="0.5" />
        <path d="M84 30 Q100 10 116 30" fill="none" stroke="#C9A84C" strokeWidth="2.5" opacity="0.7" strokeLinecap="round" />
        <path d="M72 50 L66 56" stroke="#1A1208" strokeWidth="4" />
        <path d="M128 50 L134 56" stroke="#1A1208" strokeWidth="4" />
        <path d="M70 58 L66 68 L100 76 L134 68 L130 58" fill="#1A1208" stroke="rgba(201,168,76,0.3)" strokeWidth="1.5" />
        <path d="M68 68 L64 78 L100 84 L136 78 L132 68" fill="#161008" stroke="rgba(201,168,76,0.2)" strokeWidth="1" />
      </g>

      {/* ─── Right arm raised to grip (on sword unsheathe) ─── */}
      {swordUnsheathed && (
        <g>
          {/* Override right arm — raised gripping position */}
          <rect x="126" y="78" width="18" height="48" rx="5" fill="#1A1610" stroke="#0A0806" strokeWidth="2.5" />
          <ellipse cx="138" cy="130" rx="7" ry="6" fill="#1A1610" stroke="#0A0806" strokeWidth="2" />
        </g>
      )}

      {/* ─── ARMOR SWORD — katana pointing upward (on sword unsheathe) ─── */}
      <g id="armor-sword" style={armorAppear(swordUnsheathed)}>
        {/* Blade — heavy body + thin bright edge, extending upward */}
        <line x1="142" y1="180" x2="155" y2="20" stroke="#2A2820" strokeWidth="3.5" strokeLinecap="round" />
        <line x1="143" y1="180" x2="156" y2="20" stroke="#585248" strokeWidth="0.5" strokeLinecap="round" />
        <line x1="143.5" y1="178" x2="156.5" y2="22" stroke="rgba(201,168,76,0.08)" strokeWidth="1.5" />
        {/* Tsuba guard — at grip point */}
        <ellipse cx="140" cy="175" rx="8" ry="4" fill="#1A1208" stroke="rgba(201,168,76,0.5)" strokeWidth="2" transform="rotate(6 140 175)" />
        {/* Handle — downward from tsuba */}
        <line x1="139" y1="177" x2="136" y2="210" stroke="#1A1208" strokeWidth="5" strokeLinecap="round" />
        {/* Wrap — thin detail */}
        <line x1="139" y1="177" x2="136" y2="210" stroke="rgba(201,168,76,0.2)" strokeWidth="5" strokeLinecap="round" strokeDasharray="2.5 3.5" />
        {/* Kashira pommel */}
        <ellipse cx="135" cy="212" rx="3" ry="2.5" fill="#2A1A08" stroke="#0A0806" strokeWidth="1.5" />
      </g>
    </svg>
  )
}
