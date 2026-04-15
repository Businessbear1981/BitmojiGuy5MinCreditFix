export function Scene2Koi() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1400 900"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Dark background */}
        <rect x="0" y="0" width="1400" height="900" fill="#040810" />

        {/* Moon — upper left */}
        <circle cx="200" cy="140" r="110" fill="#C8B060" opacity="0.04" />
        <circle cx="200" cy="140" r="80" fill="#C8B060" opacity="0.06" />
        <circle cx="200" cy="140" r="55" fill="#D8D4A4" opacity="0.72" />
        <circle cx="195" cy="135" r="48" fill="#E0DCC0" opacity="0.18" />

        {/* Pond — large center ellipse */}
        <ellipse cx="700" cy="540" rx="680" ry="320" fill="#060E18" />
        <ellipse cx="700" cy="540" rx="640" ry="300" fill="#081220" opacity="0.9" />

        {/* Six water shimmer lines */}
        <line x1="260" y1="420" x2="380" y2="420" stroke="#1A4A5A" strokeWidth="1" opacity="0.4" />
        <line x1="510" y1="450" x2="640" y2="450" stroke="#1A4A5A" strokeWidth="1" opacity="0.45" />
        <line x1="800" y1="430" x2="920" y2="430" stroke="#1A4A5A" strokeWidth="1" opacity="0.38" />
        <line x1="380" y1="540" x2="500" y2="540" stroke="#1A4A5A" strokeWidth="0.8" opacity="0.35" />
        <line x1="860" y1="560" x2="980" y2="560" stroke="#1A4A5A" strokeWidth="0.8" opacity="0.4" />
        <line x1="1050" y1="500" x2="1160" y2="500" stroke="#1A4A5A" strokeWidth="0.9" opacity="0.35" />

        {/* Ripple ring set 1 — left pond */}
        <ellipse cx="440" cy="520" rx="45" ry="15" fill="none" stroke="#1E4860" strokeWidth="0.9" opacity="0.4" />
        <ellipse cx="440" cy="520" rx="70" ry="22" fill="none" stroke="#1E4860" strokeWidth="0.7" opacity="0.28" />
        <ellipse cx="440" cy="520" rx="95" ry="30" fill="none" stroke="#1E4860" strokeWidth="0.5" opacity="0.18" />

        {/* Ripple ring set 2 — right pond */}
        <ellipse cx="980" cy="480" rx="40" ry="13" fill="none" stroke="#1E4860" strokeWidth="0.9" opacity="0.35" />
        <ellipse cx="980" cy="480" rx="62" ry="20" fill="none" stroke="#1E4860" strokeWidth="0.7" opacity="0.25" />
        <ellipse cx="980" cy="480" rx="84" ry="26" fill="none" stroke="#1E4860" strokeWidth="0.5" opacity="0.15" />

        {/* Moon reflection on pond surface */}
        <ellipse cx="700" cy="640" rx="42" ry="12" fill="#C8B860" opacity="0.12" />
        <ellipse cx="700" cy="640" rx="26" ry="7" fill="#D8C870" opacity="0.08" />
      </svg>
    </div>
  )
}
