export function Scene1Samurai() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
      <svg width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice">

        {/* ═══ BACKGROUND ═══ */}
        {/* Wall — top 58% */}
        <rect x="0" y="0" width="1400" height="522" fill="#0E0A06" />
        {/* Wall moonlight wash — upper right */}
        <rect x="700" y="0" width="700" height="522" fill="#120E08" opacity="0.35" />
        {/* Floor — bottom 42% */}
        <rect x="0" y="522" width="1400" height="378" fill="#0C0804" />
        {/* Floor moonlight pool area */}
        <rect x="500" y="522" width="400" height="378" fill="#100C06" opacity="0.3" />
        {/* Wall/floor divider */}
        <line x1="0" y1="522" x2="1400" y2="522" stroke="#1E1608" strokeWidth="2" />

        {/* Wall grain lines */}
        {[60, 120, 180, 240, 300, 360, 420, 480].map((y, i) => (
          <line key={`wg${i}`} x1="0" y1={y} x2="1400" y2={y} stroke="#C8A878" strokeWidth="0.3" opacity={0.04 + (i % 3) * 0.01} />
        ))}

        {/* Floor plank lines — horizontal */}
        <line x1="0" y1="560" x2="1400" y2="560" stroke="#16100A" strokeWidth="1" />
        <line x1="0" y1="620" x2="1400" y2="620" stroke="#16100A" strokeWidth="1" />
        <line x1="0" y1="690" x2="1400" y2="690" stroke="#16100A" strokeWidth="1" />
        <line x1="0" y1="770" x2="1400" y2="770" stroke="#16100A" strokeWidth="1" />
        <line x1="0" y1="850" x2="1400" y2="850" stroke="#16100A" strokeWidth="1" />
        {/* Plank vertical divisions */}
        <line x1="280" y1="522" x2="280" y2="900" stroke="#16100A" opacity="0.4" />
        <line x1="560" y1="522" x2="560" y2="900" stroke="#16100A" opacity="0.4" />
        <line x1="840" y1="522" x2="840" y2="900" stroke="#16100A" opacity="0.4" />
        <line x1="1120" y1="522" x2="1120" y2="900" stroke="#16100A" opacity="0.4" />

        {/* ═══ WASHI WALL PANELS ═══ */}
        <rect x="60" y="40" width="240" height="440" fill="#0A0806" stroke="rgba(201,168,76,0.12)" strokeWidth="0.8" />
        <rect x="320" y="40" width="240" height="440" fill="#0A0806" stroke="rgba(201,168,76,0.12)" strokeWidth="0.8" />
        <rect x="840" y="40" width="240" height="440" fill="#0A0806" stroke="rgba(201,168,76,0.14)" strokeWidth="0.8" />
        <rect x="1100" y="40" width="240" height="440" fill="#0A0806" stroke="rgba(201,168,76,0.14)" strokeWidth="0.8" />

        {/* Panel cross members */}
        <line x1="60" y1="260" x2="300" y2="260" stroke="rgba(201,168,76,0.08)" strokeWidth="0.5" />
        <line x1="320" y1="260" x2="560" y2="260" stroke="rgba(201,168,76,0.08)" strokeWidth="0.5" />
        <line x1="840" y1="260" x2="1080" y2="260" stroke="rgba(201,168,76,0.08)" strokeWidth="0.5" />
        <line x1="1100" y1="260" x2="1340" y2="260" stroke="rgba(201,168,76,0.08)" strokeWidth="0.5" />

        {/* ═══ MOON WINDOW ═══ */}
        <rect x="640" y="40" width="120" height="130" fill="#0A0806" stroke="rgba(201,168,76,0.3)" strokeWidth="1" />
        <line x1="700" y1="40" x2="700" y2="170" stroke="rgba(201,168,76,0.2)" strokeWidth="0.6" />
        <line x1="640" y1="105" x2="760" y2="105" stroke="rgba(201,168,76,0.2)" strokeWidth="0.6" />
        <circle cx="700" cy="105" r="50" fill="#E8E0B0" opacity="0.65" />
        <circle cx="695" cy="100" r="44" fill="#F0E8C8" opacity="0.2" />
        <circle cx="700" cy="105" r="70" fill="rgba(232,224,176,0.04)" />

        {/* Moonlight shaft to floor */}
        <path d="M655 170 L590 600 L810 600 L745 170 Z" fill="rgba(232,224,176,0.012)" />
        <ellipse cx="700" cy="620" rx="90" ry="28" fill="#E8E0B0" opacity="0.05" />
        <ellipse cx="700" cy="620" rx="55" ry="18" fill="#E8E0B0" opacity="0.04" />

        {/* ═══ ARMOR STAND ═══ */}
        {/* Base */}
        <rect x="640" y="488" width="120" height="14" rx="2" fill="#2A1A08" />
        <line x1="640" y1="488" x2="760" y2="488" stroke="#3A2A14" strokeWidth="0.5" />
        {/* Vertical poles */}
        <line x1="670" y1="200" x2="670" y2="488" stroke="#2A1A08" strokeWidth="6" />
        <line x1="730" y1="200" x2="730" y2="488" stroke="#2A1A08" strokeWidth="6" />
        {/* Cross brace */}
        <line x1="670" y1="400" x2="730" y2="400" stroke="#2A1A08" strokeWidth="4" />
        {/* Shoulder bar */}
        <rect x="620" y="196" width="160" height="8" rx="2" fill="#362010" />

        {/* Kabuto helmet on stand */}
        <ellipse cx="700" cy="180" rx="52" ry="36" fill="#1A1208" stroke="#C9A84C" strokeWidth="1" />
        <ellipse cx="700" cy="174" rx="40" ry="26" fill="#242018" />
        <path d="M664 176 Q700 150 736 176" fill="none" stroke="rgba(201,168,76,0.25)" strokeWidth="0.6" />
        {/* Maedate crescent */}
        <path d="M676 152 Q700 120 724 152" fill="none" stroke="#C9A84C" strokeWidth="2.5" opacity="0.75" strokeLinecap="round" />
        {/* Shikoro neck plates */}
        <path d="M646 194 Q640 204 640 212 Q670 220 700 222 Q730 220 760 212 Q760 204 754 194" fill="#1A1208" stroke="rgba(201,168,76,0.25)" strokeWidth="0.6" />
        <path d="M642 212 Q638 220 638 226 Q668 234 700 236 Q732 234 762 226 Q762 220 758 212" fill="#161008" stroke="rgba(201,168,76,0.18)" strokeWidth="0.5" />

        {/* Do chest plate on stand */}
        <rect x="654" y="240" width="92" height="120" rx="4" fill="#1E1810" stroke="rgba(201,168,76,0.35)" strokeWidth="0.8" />
        <line x1="658" y1="262" x2="742" y2="262" stroke="rgba(201,168,76,0.25)" strokeWidth="0.5" />
        <line x1="658" y1="280" x2="742" y2="280" stroke="rgba(201,168,76,0.22)" strokeWidth="0.5" />
        <line x1="658" y1="298" x2="742" y2="298" stroke="rgba(201,168,76,0.2)" strokeWidth="0.5" />
        <line x1="658" y1="316" x2="742" y2="316" stroke="rgba(201,168,76,0.18)" strokeWidth="0.5" />
        <line x1="658" y1="334" x2="742" y2="334" stroke="rgba(201,168,76,0.15)" strokeWidth="0.5" />
        <circle cx="700" cy="295" r="16" fill="none" stroke="rgba(201,168,76,0.4)" strokeWidth="0.8" />
        <circle cx="700" cy="295" r="7" fill="rgba(201,168,76,0.18)" />

        {/* Katana leaning against stand */}
        <line x1="782" y1="215" x2="812" y2="480" stroke="#2A2820" strokeWidth="3" strokeLinecap="round" />
        <line x1="783" y1="215" x2="813" y2="480" stroke="#585248" strokeWidth="1" strokeLinecap="round" />
        <ellipse cx="808" cy="460" rx="12" ry="6" fill="#1A1208" stroke="rgba(201,168,76,0.4)" strokeWidth="0.8" transform="rotate(-10 808 460)" />
        <line x1="810" y1="462" x2="820" y2="500" stroke="#1A1208" strokeWidth="5" strokeLinecap="round" />
        <line x1="810" y1="462" x2="820" y2="500" stroke="rgba(201,168,76,0.2)" strokeWidth="5" strokeLinecap="round" strokeDasharray="3 4" />
        <ellipse cx="821" cy="502" rx="4" ry="3" fill="#2A1A08" />

        {/* ═══ CANDLES — LEFT CLUSTER ═══ */}
        <ellipse cx="170" cy="490" rx="100" ry="65" fill="rgba(201,168,76,0.04)" />
        <ellipse cx="170" cy="490" rx="65" ry="42" fill="rgba(208,176,96,0.06)" />
        <ellipse cx="170" cy="490" rx="35" ry="22" fill="rgba(240,208,128,0.08)" />
        {/* Candle 1 */}
        <rect x="148" y="464" width="10" height="30" rx="1" fill="#2A2010" />
        <path d="M150 464 Q153 450 156 464" fill="#D0B060" />
        <path d="M151 462 Q153 454 155 460" stroke="#F0D080" strokeWidth="0.6" fill="none" />
        {/* Candle 2 */}
        <rect x="170" y="470" width="10" height="24" rx="1" fill="#2A2010" />
        <path d="M172 470 Q175 458 178 470" fill="#D0B060" />
        <path d="M173 468 Q175 461 177 466" stroke="#F0D080" strokeWidth="0.6" fill="none" />
        {/* Candle 3 */}
        <rect x="190" y="468" width="10" height="26" rx="1" fill="#2A2010" />
        <path d="M192 468 Q195 455 198 468" fill="#D0B060" />
        <path d="M193 466 Q195 459 197 464" stroke="#F0D080" strokeWidth="0.6" fill="none" />

        {/* ═══ CANDLES — RIGHT CLUSTER ═══ */}
        <ellipse cx="1230" cy="490" rx="100" ry="65" fill="rgba(201,168,76,0.04)" />
        <ellipse cx="1230" cy="490" rx="65" ry="42" fill="rgba(208,176,96,0.06)" />
        <ellipse cx="1230" cy="490" rx="35" ry="22" fill="rgba(240,208,128,0.08)" />
        <rect x="1208" y="464" width="10" height="30" rx="1" fill="#2A2010" />
        <path d="M1210 464 Q1213 450 1216 464" fill="#D0B060" />
        <path d="M1211 462 Q1213 454 1215 460" stroke="#F0D080" strokeWidth="0.6" fill="none" />
        <rect x="1230" y="470" width="10" height="24" rx="1" fill="#2A2010" />
        <path d="M1232 470 Q1235 458 1238 470" fill="#D0B060" />
        <path d="M1233 468 Q1235 461 1237 466" stroke="#F0D080" strokeWidth="0.6" fill="none" />
        <rect x="1250" y="468" width="10" height="26" rx="1" fill="#2A2010" />
        <path d="M1252 468 Q1255 455 1258 468" fill="#D0B060" />
        <path d="M1253 466 Q1255 459 1257 464" stroke="#F0D080" strokeWidth="0.6" fill="none" />

        {/* ═══ OMINOUS WALL SHADOW ═══ */}
        <path d="M420 200 Q400 230 408 290 Q388 330 398 390 Q380 420 392 460" fill="none" stroke="#020106" strokeWidth="20" opacity="0.35" strokeLinecap="round" />

        {/* ═══ GROUND MIST ═══ */}
        <ellipse cx="250" cy="860" rx="240" ry="24" fill="#0A0806" opacity="0.55" />
        <ellipse cx="700" cy="870" rx="320" ry="20" fill="#0A0806" opacity="0.55" />
        <ellipse cx="1150" cy="858" rx="240" ry="22" fill="#0A0806" opacity="0.55" />

        {/* ═══ CORNER VIGNETTE ═══ */}
        <ellipse cx="0" cy="0" rx="340" ry="280" fill="#020106" opacity="0.7" />
        <ellipse cx="1400" cy="0" rx="320" ry="260" fill="#020106" opacity="0.7" />
        <ellipse cx="0" cy="900" rx="360" ry="300" fill="#020106" opacity="0.7" />
        <ellipse cx="1400" cy="900" rx="340" ry="280" fill="#020106" opacity="0.7" />

        {/* Cold blue cast */}
        <rect x="0" y="0" width="1400" height="900" fill="#0A0818" opacity="0.06" />
      </svg>
    </div>
  )
}
