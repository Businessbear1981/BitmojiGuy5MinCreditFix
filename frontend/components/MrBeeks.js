"use client";

/**
 * Mr. Beeks — The Warrior
 *
 * Central hero of the BitmojiGuy experience.
 * Visual representation of the user's credit repair journey.
 * Grows stronger through 5 armor stages.
 *
 * Stage 0: Base (no armor, 60% opacity)
 * Stage 1: Arm Guards (Kote) — Dojo complete
 * Stage 2: Chest Plate (Do) — Documents uploaded
 * Stage 3: Leg Guards (Suneate) — Disputes reviewed
 * Stage 4: Helmet (Kabuto) — Payment authorized
 * Stage 5: Sword (Katana) — Disputes released
 */

const SIZES = {
  small: { width: 120, height: 180 },
  medium: { width: 160, height: 240 },
  large: { width: 200, height: 300 },
};

export default function MrBeeks({ stage = 0, size = "medium" }) {
  const dim = SIZES[size] || SIZES.medium;
  const opacity = stage === 0 ? 0.6 : stage === 1 ? 0.8 : stage === 2 ? 0.9 : 1;

  return (
    <div className="warrior-container" style={{ width: dim.width, height: dim.height }}>
      {/* Glow aura — intensifies with stage */}
      <div
        className="warrior-glow"
        style={{ opacity: 0.15 + stage * 0.1 }}
      />

      {/* Warrior SVG */}
      <svg
        viewBox="0 0 200 300"
        width={dim.width}
        height={dim.height}
        className="warrior-figure"
        style={{ opacity }}
        aria-label={`Mr. Beeks warrior — stage ${stage} of 5`}
        role="img"
      >
        {/* Base — dark tunic warrior */}
        <g id="base">
          {/* Head */}
          <ellipse cx="100" cy="52" rx="22" ry="26" fill="#C9A876" />
          {/* Eyes */}
          <ellipse cx="91" cy="48" rx="3" ry="2.5" fill="#D4AF37" />
          <ellipse cx="109" cy="48" rx="3" ry="2.5" fill="#D4AF37" />
          {/* Hair */}
          <path d="M78 38 Q80 20 100 18 Q120 20 122 38 Q115 28 100 26 Q85 28 78 38Z" fill="#1A1A1A" />
          {/* Neck */}
          <rect x="94" y="76" width="12" height="10" fill="#C9A876" rx="2" />
          {/* Body — tunic */}
          <path d="M72 86 L128 86 L132 200 L68 200Z" fill="#2C3E50" />
          {/* Belt */}
          <rect x="70" y="155" width="60" height="8" fill="#1A1A1A" rx="2" />
          {/* Arms */}
          <path d="M72 86 L52 150 L58 152 L76 96Z" fill="#2C3E50" />
          <path d="M128 86 L148 150 L142 152 L124 96Z" fill="#2C3E50" />
          {/* Hands */}
          <circle cx="55" cy="153" r="6" fill="#C9A876" />
          <circle cx="145" cy="153" r="6" fill="#C9A876" />
          {/* Legs */}
          <path d="M78 200 L74 270 L86 270 L90 200Z" fill="#2C3E50" />
          <path d="M110 200 L114 270 L126 270 L122 200Z" fill="#2C3E50" />
          {/* Feet */}
          <ellipse cx="80" cy="274" rx="10" ry="5" fill="#3A3A3A" />
          <ellipse cx="120" cy="274" rx="10" ry="5" fill="#3A3A3A" />
        </g>

        {/* Stage 1: Arm Guards (Kote) */}
        {stage >= 1 && (
          <g id="armor-stage-1" className="animate-[armor-materialize_0.8s_ease-out]">
            <rect x="52" y="110" width="14" height="35" rx="4" fill="#3A3A3A" stroke="#D4AF37" strokeWidth="1" />
            <rect x="134" y="110" width="14" height="35" rx="4" fill="#3A3A3A" stroke="#D4AF37" strokeWidth="1" />
            {/* Gold accents */}
            <rect x="54" y="112" width="10" height="3" rx="1" fill="#D4AF37" opacity="0.7" />
            <rect x="136" y="112" width="10" height="3" rx="1" fill="#D4AF37" opacity="0.7" />
            <rect x="54" y="140" width="10" height="3" rx="1" fill="#D4AF37" opacity="0.7" />
            <rect x="136" y="140" width="10" height="3" rx="1" fill="#D4AF37" opacity="0.7" />
          </g>
        )}

        {/* Stage 2: Chest Plate (Do) */}
        {stage >= 2 && (
          <g id="armor-stage-2" className="animate-[armor-materialize_0.8s_ease-out_0.2s]">
            <path d="M76 90 L124 90 L128 155 L72 155Z" fill="#3A3A3A" stroke="#D4AF37" strokeWidth="1" />
            {/* Layered plates */}
            <path d="M80 95 L120 95 L122 115 L78 115Z" fill="#4A4A4A" />
            <path d="M78 118 L122 118 L124 138 L76 138Z" fill="#4A4A4A" />
            {/* Gold rivets */}
            <circle cx="82" cy="98" r="2" fill="#D4AF37" />
            <circle cx="118" cy="98" r="2" fill="#D4AF37" />
            <circle cx="100" cy="105" r="2.5" fill="#D4AF37" />
            <circle cx="82" cy="122" r="2" fill="#D4AF37" />
            <circle cx="118" cy="122" r="2" fill="#D4AF37" />
          </g>
        )}

        {/* Stage 3: Leg Guards (Suneate) */}
        {stage >= 3 && (
          <g id="armor-stage-3" className="animate-[armor-materialize_0.8s_ease-out_0.4s]">
            <rect x="74" y="210" width="16" height="50" rx="4" fill="#3A3A3A" stroke="#D4AF37" strokeWidth="1" />
            <rect x="110" y="210" width="16" height="50" rx="4" fill="#3A3A3A" stroke="#D4AF37" strokeWidth="1" />
            {/* Leather straps */}
            <rect x="76" y="220" width="12" height="3" rx="1" fill="#8B6914" />
            <rect x="112" y="220" width="12" height="3" rx="1" fill="#8B6914" />
            <rect x="76" y="240" width="12" height="3" rx="1" fill="#8B6914" />
            <rect x="112" y="240" width="12" height="3" rx="1" fill="#8B6914" />
            {/* Gold trim */}
            <rect x="76" y="255" width="12" height="2" fill="#D4AF37" opacity="0.6" />
            <rect x="112" y="255" width="12" height="2" fill="#D4AF37" opacity="0.6" />
          </g>
        )}

        {/* Stage 4: Helmet (Kabuto) */}
        {stage >= 4 && (
          <g id="armor-stage-4" className="animate-[armor-materialize_0.8s_ease-out_0.6s]">
            <path d="M72 42 Q72 12 100 8 Q128 12 128 42 L122 45 Q120 20 100 16 Q80 20 78 45Z" fill="#3A3A3A" stroke="#D4AF37" strokeWidth="1" />
            {/* Face guard */}
            <path d="M82 55 L92 62 L100 58 L108 62 L118 55" fill="none" stroke="#D4AF37" strokeWidth="1.5" />
            {/* Gold crest */}
            <path d="M96 10 L100 0 L104 10" fill="#D4AF37" />
            <circle cx="100" cy="12" r="3" fill="#D4AF37" />
          </g>
        )}

        {/* Stage 5: Sword (Katana) */}
        {stage >= 5 && (
          <g id="armor-stage-5" className="animate-[armor-materialize_0.8s_ease-out_0.8s]">
            {/* Handle */}
            <rect x="146" y="95" width="5" height="30" rx="2" fill="#8B6914" />
            {/* Handle wrap (gold) */}
            <rect x="147" y="98" width="3" height="3" fill="#D4AF37" />
            <rect x="147" y="104" width="3" height="3" fill="#D4AF37" />
            <rect x="147" y="110" width="3" height="3" fill="#D4AF37" />
            <rect x="147" y="116" width="3" height="3" fill="#D4AF37" />
            {/* Guard (tsuba) */}
            <ellipse cx="148" cy="93" rx="8" ry="4" fill="#D4AF37" />
            {/* Blade */}
            <path d="M146 93 L148 15 L150 93Z" fill="#E8E8E8" opacity="0.9" />
            {/* Blade highlight */}
            <path d="M147.5 93 L148 25 L148.5 93Z" fill="white" opacity="0.3" />
          </g>
        )}

        {/* Spark particles on stage >= 1 */}
        {stage >= 1 && (
          <g id="sparks">
            <circle cx="85" cy="100" r="2" fill="#D4AF37" className="animate-spark" style={{ animationDelay: '0s' }} />
            <circle cx="115" cy="95" r="2" fill="#D4AF37" className="animate-spark" style={{ animationDelay: '0.1s' }} />
            <circle cx="100" cy="80" r="1.5" fill="#D4AF37" className="animate-spark" style={{ animationDelay: '0.2s' }} />
            <circle cx="90" cy="140" r="2" fill="#D4AF37" className="animate-spark" style={{ animationDelay: '0.3s' }} />
            <circle cx="110" cy="130" r="1.5" fill="#D4AF37" className="animate-spark" style={{ animationDelay: '0.15s' }} />
          </g>
        )}
      </svg>
    </div>
  );
}
