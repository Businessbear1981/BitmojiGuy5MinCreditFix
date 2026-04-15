export function Scene5Gate() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
      {/* Meshy 3D render background */}
      <img
        src="/scenes/scene5.png"
        alt=""
        style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'cover', objectPosition: 'center',
          filter: 'brightness(0.55) contrast(1.3) saturate(0.85)',
        }}
      />
      {/* Dark overlay */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(8,6,4,0.45)' }} />
      {/* SVG overlay — dragon presence + petal drift */}
      <svg width="100%" height="100%" viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice" style={{ position: 'absolute', inset: 0 }}>
        {/* Ancient presence beyond gate */}
        <path d="M420 300 Q400 340 410 400 Q390 450 405 520 Q380 560 400 620 Q420 660 460 680 Q520 700 580 690 Q620 680 640 650 Q660 600 650 540 Q660 480 640 420 Q650 360 630 310 Q600 280 560 270 Q500 260 460 275 Q440 280 420 300 Z" fill="#020208" opacity="0.2" />
        <path d="M450 360 Q440 400 450 460 Q435 500 448 560 Q470 600 520 610 Q570 605 590 570 Q600 520 595 460 Q605 400 590 350 Q560 320 510 315 Q470 320 450 360 Z" fill="#020208" opacity="0.12" />
        {/* Red eyes */}
        <circle cx="490" cy="380" r="3" fill="#8B1A1A" opacity="0.4" />
        <circle cx="530" cy="378" r="3" fill="#8B1A1A" opacity="0.4" />
        <circle cx="490" cy="380" r="6" fill="#8B1A1A" opacity="0.06" />
        <circle cx="530" cy="378" r="6" fill="#8B1A1A" opacity="0.06" />
        {/* Darkened petals near the shape */}
        <ellipse cx="440" cy="340" rx="4" ry="2.5" fill="#8B2252" opacity="0.5" transform="rotate(25 440 340)" />
        <ellipse cx="560" cy="360" rx="3.5" ry="2" fill="#8B2252" opacity="0.45" transform="rotate(-15 560 360)" />
        <ellipse cx="480" cy="420" rx="4" ry="2.5" fill="#8B2252" opacity="0.4" transform="rotate(35 480 420)" />
        <ellipse cx="520" cy="480" rx="3" ry="2" fill="#8B2252" opacity="0.35" transform="rotate(-20 520 480)" />
        <ellipse cx="470" cy="520" rx="3.5" ry="2" fill="#8B2252" opacity="0.3" transform="rotate(10 470 520)" />
        {/* Ground mist */}
        <ellipse cx="700" cy="800" rx="500" ry="30" fill="#0C0A06" opacity="0.5" />
        <ellipse cx="300" cy="820" rx="200" ry="20" fill="#0C0A06" opacity="0.3" />
        <ellipse cx="1100" cy="810" rx="250" ry="25" fill="#0C0A06" opacity="0.35" />
      </svg>
    </div>
  )
}
