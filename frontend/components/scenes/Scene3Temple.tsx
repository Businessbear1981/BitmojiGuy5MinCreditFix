export function Scene3Temple() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1400 900"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Dark sky */}
        <rect x="0" y="0" width="1400" height="900" fill="#080A14" />
        <ellipse cx="1100" cy="140" rx="400" ry="260" fill="#0C1020" opacity="0.4" />

        {/* Moon — upper right */}
        <circle cx="1100" cy="140" r="85" fill="#C8B060" opacity="0.04" />
        <circle cx="1100" cy="140" r="60" fill="#D8D4A4" opacity="0.74" />
        <circle cx="1095" cy="135" r="52" fill="#E0DCC0" opacity="0.15" />

        {/* Stars */}
        <circle cx="180" cy="100" r="1" fill="#D0C890" opacity="0.3" />
        <circle cx="420" cy="60" r="0.8" fill="#D0C890" opacity="0.25" />
        <circle cx="680" cy="130" r="1.2" fill="#D0C890" opacity="0.3" />
        <circle cx="900" cy="80" r="0.7" fill="#D0C890" opacity="0.2" />
        <circle cx="1300" cy="220" r="1" fill="#D0C890" opacity="0.25" />
        <circle cx="260" cy="200" r="0.6" fill="#D0C890" opacity="0.2" />
        <circle cx="560" cy="60" r="1" fill="#D0C890" opacity="0.3" />

        {/* Misty mountain silhouette */}
        <path
          d="M0 340 Q200 220 400 290 Q600 200 800 260 Q1000 180 1200 240 Q1350 200 1400 260 L1400 440 L0 440 Z"
          fill="#0C0E18"
        />
        <path
          d="M0 350 Q200 240 400 300 Q600 220 800 270 Q1000 200 1200 250 Q1350 220 1400 270"
          fill="none"
          stroke="#141828"
          strokeWidth="1"
          opacity="0.5"
        />

        {/* Mist bands across mid */}
        <ellipse cx="700" cy="540" rx="500" ry="22" fill="#0A0C14" opacity="0.55" />
        <ellipse cx="400" cy="620" rx="350" ry="18" fill="#0A0C14" opacity="0.4" />
        <ellipse cx="1000" cy="600" rx="320" ry="15" fill="#0A0C14" opacity="0.45" />

        {/* Steep temple steps — narrowing to top */}
        {[
          { y: 820, w: 640, h: 40, front: '#1A1810', top: '#26241A' },
          { y: 780, w: 560, h: 36, front: '#181610', top: '#24221A' },
          { y: 744, w: 490, h: 34, front: '#1A1810', top: '#26241A' },
          { y: 710, w: 420, h: 32, front: '#161410', top: '#222018' },
          { y: 678, w: 360, h: 30, front: '#1A1810', top: '#26241A' },
          { y: 648, w: 300, h: 28, front: '#161410', top: '#222018' },
          { y: 620, w: 250, h: 26, front: '#1A1810', top: '#26241A' },
          { y: 594, w: 210, h: 24, front: '#161410', top: '#222018' },
          { y: 570, w: 175, h: 22, front: '#1A1810', top: '#26241A' },
          { y: 548, w: 145, h: 20, front: '#161410', top: '#222018' },
          { y: 528, w: 115, h: 18, front: '#1A1810', top: '#26241A' },
          { y: 510, w: 88, h: 16, front: '#161410', top: '#222018' },
          { y: 494, w: 66, h: 14, front: '#1A1810', top: '#26241A' },
          { y: 480, w: 48, h: 12, front: '#161410', top: '#222018' },
        ].map((s, i) => {
          const x = 700 - s.w / 2
          return (
            <g key={`step${i}`}>
              {/* Front face */}
              <rect x={x} y={s.y} width={s.w} height={s.h} fill={s.front} />
              {/* Top — catches moonlight */}
              <polygon
                points={`${x},${s.y} ${x + s.w},${s.y} ${x + s.w - 8},${s.y - 10} ${x + 8},${s.y - 10}`}
                fill={s.top}
              />
              {/* Gold edge accent (faint) */}
              <line x1={x} y1={s.y} x2={x + s.w} y2={s.y} stroke="rgba(201,168,76,0.08)" strokeWidth="0.5" />
              {/* Moonlight edge highlight on right */}
              <line x1={x + s.w} y1={s.y} x2={x + s.w} y2={s.y + s.h} stroke="#2A2818" strokeWidth="0.5" opacity="0.5" />
            </g>
          )
        })}

        {/* Pine trees — LEFT side */}
        {/* Trunk */}
        <path d="M80 450 Q78 560 85 700 Q87 770 82 860" fill="none" stroke="#1A120A" strokeWidth="10" strokeLinecap="round" />
        <path d="M82 450 Q80 560 87 700" fill="none" stroke="#241A10" strokeWidth="2.5" opacity="0.4" />
        {/* Foliage clusters */}
        <ellipse cx="50" cy="420" rx="40" ry="34" fill="#0E1A0C" />
        <ellipse cx="52" cy="416" rx="34" ry="28" fill="#142010" opacity="0.5" />
        <ellipse cx="100" cy="440" rx="35" ry="30" fill="#0E1A0C" />
        <ellipse cx="102" cy="436" rx="28" ry="24" fill="#142010" opacity="0.4" />
        <ellipse cx="65" cy="470" rx="30" ry="26" fill="#0C180A" />
        <ellipse cx="115" cy="480" rx="26" ry="22" fill="#0C180A" opacity="0.9" />

        {/* Pine trees — RIGHT side */}
        <path d="M1320 450 Q1322 560 1316 700 Q1314 770 1319 860" fill="none" stroke="#1A120A" strokeWidth="10" strokeLinecap="round" />
        <path d="M1318 450 Q1320 560 1314 700" fill="none" stroke="#241A10" strokeWidth="2.5" opacity="0.4" />
        <ellipse cx="1350" cy="420" rx="40" ry="34" fill="#0E1A0C" />
        <ellipse cx="1352" cy="416" rx="34" ry="28" fill="#142010" opacity="0.5" />
        <ellipse cx="1300" cy="440" rx="35" ry="30" fill="#0E1A0C" />
        <ellipse cx="1302" cy="436" rx="28" ry="24" fill="#142010" opacity="0.4" />
        <ellipse cx="1335" cy="470" rx="30" ry="26" fill="#0C180A" />
        <ellipse cx="1285" cy="480" rx="26" ry="22" fill="#0C180A" opacity="0.9" />

        {/* Stone lanterns flanking path */}
        <rect x="190" y="660" width="14" height="30" fill="#1A1810" />
        <rect x="186" y="650" width="22" height="12" fill="#201E14" />
        <polygon points="183,650 211,650 197,638" fill="#26241A" />
        <ellipse cx="197" cy="675" rx="4" ry="5" fill="rgba(201,168,76,0.15)" />
        <ellipse cx="197" cy="675" rx="18" ry="14" fill="rgba(201,168,76,0.04)" />

        <rect x="1196" y="660" width="14" height="30" fill="#1A1810" />
        <rect x="1192" y="650" width="22" height="12" fill="#201E14" />
        <polygon points="1189,650 1217,650 1203,638" fill="#26241A" />
        <ellipse cx="1203" cy="675" rx="4" ry="5" fill="rgba(201,168,76,0.15)" />
        <ellipse cx="1203" cy="675" rx="18" ry="14" fill="rgba(201,168,76,0.04)" />

        {/* TWO CLIMBING FIGURES */}
        {/* Figure 1 — lower left, larger */}
        <g>
          {/* Straw hat */}
          <ellipse cx="560" cy="740" rx="14" ry="5" fill="#0C0A08" />
          <path d="M546 740 Q560 732 574 740" fill="#0A0806" />
          {/* Body */}
          <ellipse cx="560" cy="758" rx="9" ry="13" fill="#0C0A08" />
          {/* Legs */}
          <path d="M554 770 L550 790" stroke="#0C0A08" strokeWidth="3" strokeLinecap="round" />
          <path d="M566 770 L570 790" stroke="#0C0A08" strokeWidth="3" strokeLinecap="round" />
          {/* Arm with bucket */}
          <path d="M570 753 L580 748" stroke="#0C0A08" strokeWidth="2.5" strokeLinecap="round" />
          <rect x="578" y="746" width="6" height="10" rx="1" fill="#0C0A08" />
          <line x1="578" y1="746" x2="584" y2="746" stroke="#2A2418" strokeWidth="0.5" />
        </g>

        {/* Figure 2 — higher right, smaller (perspective) */}
        <g>
          <ellipse cx="770" cy="640" rx="10" ry="4" fill="#0C0A08" />
          <path d="M760 640 Q770 634 780 640" fill="#0A0806" />
          <ellipse cx="770" cy="653" rx="7" ry="10" fill="#0C0A08" />
          <path d="M766 662 L763 676" stroke="#0C0A08" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M774 662 L777 676" stroke="#0C0A08" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M778 650 L786 646" stroke="#0C0A08" strokeWidth="2" strokeLinecap="round" />
        </g>

        {/* Temple at top */}
        {/* Body */}
        <rect x="672" y="452" width="56" height="28" fill="#0A0808" />
        {/* Roof */}
        <path d="M660 452 Q700 428 740 452" fill="#0A0808" />
        <path d="M662 452 Q700 434 738 452" fill="none" stroke="#141210" strokeWidth="0.6" />
        {/* Roof curl ends */}
        <path d="M660 452 L656 456" stroke="#0A0808" strokeWidth="2" strokeLinecap="round" />
        <path d="M740 452 L744 456" stroke="#0A0808" strokeWidth="2" strokeLinecap="round" />
        {/* Faint red inner glow */}
        <ellipse cx="700" cy="466" rx="16" ry="6" fill="#8B1A1A" opacity="0.06" />

        {/* Corner vignette */}
        <ellipse cx="0" cy="0" rx="340" ry="280" fill="#020106" opacity="0.7" />
        <ellipse cx="1400" cy="0" rx="320" ry="260" fill="#020106" opacity="0.6" />
        <ellipse cx="0" cy="900" rx="380" ry="320" fill="#020106" opacity="0.7" />
        <ellipse cx="1400" cy="900" rx="360" ry="300" fill="#020106" opacity="0.7" />
      </svg>
    </div>
  )
}
