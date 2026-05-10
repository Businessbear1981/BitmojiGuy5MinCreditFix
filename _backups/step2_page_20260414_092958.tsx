'use client'

import { useState, useEffect, useRef } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { useWizardStore } from '@/store/wizardStore'
import { Scene2Koi } from '@/components/scenes/Scene2Koi'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { ArmorWarrior } from '@/components/warrior/ArmorWarrior'

const MASCOT_SPEECH = [
  'Upload each document. Watch the warrior dress for battle. The sword is last.',
  'Identity confirmed — the 胴 Do chest plate is on. Two more pieces before the sword.',
  'Address verified — 籠手 Kote arm guards equipped. One more piece. Almost there.',
  'Credit report parsed — 兜 Kabuto helmet on. All three documents received. Unsheathe the sword.',
  '⚔ Fully armed. The warrior is ready. The bureaus have no defense.',
]

export default function Step2Page() {
  const { navigateTo } = useShojiNav()
  const { uploads, setUpload } = useWizardStore()
  const [pieces, setPieces] = useState<string[]>([])
  const [swordOverlay, setSwordOverlay] = useState(false)
  const [swordVisible, setSwordVisible] = useState(false)
  const [swordReady, setSwordReady] = useState(false)
  const [showVerse, setShowVerse] = useState(false)
  const [showSendMe, setShowSendMe] = useState(false)
  const [lightningFlash, setLightningFlash] = useState(false)
  const [equipFlash, setEquipFlash] = useState(false)
  const swordTriggered = useRef(false)

  const uploadCount = [uploads.idUploaded, uploads.addressUploaded, uploads.reportUploaded].filter(Boolean).length
  const speechIndex = uploads.swordUnsheathed ? 4 : uploadCount

  function addPiece(piece: string) {
    setPieces(prev => prev.includes(piece) ? prev : [...prev, piece])
    // White flash on each equip
    setEquipFlash(true)
    setTimeout(() => setEquipFlash(false), 80)
  }

  // When all 3 armor pieces equipped, trigger sword ceremony
  useEffect(() => {
    const hasAll = pieces.includes('breastplate') && pieces.includes('legs') && pieces.includes('helmet')
    if (hasAll && !swordTriggered.current) {
      swordTriggered.current = true
      // 800ms delay, then fade in overlay
      setTimeout(() => {
        setSwordOverlay(true)
        setSwordVisible(true)
      }, 800)
      // 800 + 1500ms = add sword to pieces
      setTimeout(() => {
        setPieces(prev => [...prev, 'sword'])
        setUpload('swordUnsheathed', true)
        // Fade out overlay after sword equips
        setTimeout(() => {
          setSwordVisible(false)
          setTimeout(() => setSwordOverlay(false), 1000)
        }, 800)
        // Show gold text below warrior
        setTimeout(() => setSwordReady(true), 400)
        // Show verse overlay
        setTimeout(() => setShowVerse(true), 600)
      }, 2300)
    }
  }, [pieces, setUpload])

  function handleSlotUpload(key: 'idUploaded' | 'addressUploaded' | 'reportUploaded') {
    setUpload(key, true)
  }

  function handleUnsheathe() {
    if (uploadCount === 3) {
      setUpload('swordUnsheathed', true)
    }
  }

  return (
    <div style={{ minHeight: '100vh', position: 'relative', overflow: 'hidden', background: 'rgba(4,10,14,1)' }}>
      {/* Scene background */}
      <Scene2Koi />

      {/* Giant kanji watermark */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
        fontSize: '40vw', fontFamily: 'serif', color: 'rgba(29,158,117,0.04)',
        lineHeight: 1, userSelect: 'none', pointerEvents: 'none', zIndex: 1,
      }}>水</div>

      {/* Sword ceremony overlay */}
      {swordOverlay && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 30,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          opacity: swordVisible ? 1 : 0,
          transition: 'opacity 1s ease',
          pointerEvents: 'none',
        }}>
          {/* Crossed swords X */}
          <svg width="200" height="200" viewBox="0 0 200 200" style={{ opacity: swordVisible ? 1 : 0, transition: 'opacity 0.8s ease 0.3s' }}>
            {/* Sword 1 — top-left to bottom-right */}
            <line x1="30" y1="20" x2="170" y2="180" stroke="#8A8880" strokeWidth="3" strokeLinecap="round" />
            <line x1="31" y1="20" x2="171" y2="180" stroke="#C8C4B8" strokeWidth="1" strokeLinecap="round" />
            {/* Sword 1 guard */}
            <ellipse cx="55" cy="45" rx="8" ry="4" fill="none" stroke="#C9A84C" strokeWidth="0.8" transform="rotate(-45 55 45)" />
            {/* Sword 1 handle */}
            <line x1="30" y1="20" x2="18" y2="8" stroke="#2A1A08" strokeWidth="4" strokeLinecap="round" />
            <line x1="30" y1="20" x2="18" y2="8" stroke="rgba(201,168,76,0.25)" strokeWidth="4" strokeLinecap="round" strokeDasharray="2 3" />

            {/* Sword 2 — top-right to bottom-left */}
            <line x1="170" y1="20" x2="30" y2="180" stroke="#8A8880" strokeWidth="3" strokeLinecap="round" />
            <line x1="169" y1="20" x2="29" y2="180" stroke="#C8C4B8" strokeWidth="1" strokeLinecap="round" />
            {/* Sword 2 guard */}
            <ellipse cx="145" cy="45" rx="8" ry="4" fill="none" stroke="#C9A84C" strokeWidth="0.8" transform="rotate(45 145 45)" />
            {/* Sword 2 handle */}
            <line x1="170" y1="20" x2="182" y2="8" stroke="#2A1A08" strokeWidth="4" strokeLinecap="round" />
            <line x1="170" y1="20" x2="182" y2="8" stroke="rgba(201,168,76,0.25)" strokeWidth="4" strokeLinecap="round" strokeDasharray="2 3" />

            {/* Center glow */}
            <circle cx="100" cy="100" r="16" fill="rgba(201,168,76,0.06)" />
          </svg>
        </div>
      )}

      {/* Verse overlay — click to hear */}
      {showVerse && (
        <div
          onClick={() => {
            const u1 = new SpeechSynthesisUtterance('そのとき、私は主の御声を聞いた。だれを遣わそうか。')
            u1.lang = 'ja-JP'
            u1.rate = 0.75
            u1.pitch = 0.8
            u1.volume = 1
            u1.onend = () => {
              const u2 = new SpeechSynthesisUtterance('だれがわれわれのために行くだろうか。ここに私がおります。私を遣わしてください。')
              u2.lang = 'ja-JP'
              u2.rate = 0.75
              u2.pitch = 0.8
              u2.volume = 1
              u2.onend = () => {
                // 1.5s silence then SEND ME
                setTimeout(() => {
                  const u3 = new SpeechSynthesisUtterance('SEND ME')
                  u3.lang = 'en-US'
                  u3.rate = 0.5
                  u3.pitch = 0.2
                  u3.volume = 1
                  speechSynthesis.speak(u3)
                  // Slam text + lightning simultaneously
                  setShowSendMe(true)
                  setLightningFlash(true)
                  setTimeout(() => setLightningFlash(false), 200)
                  // Hold 1.8s then gone instantly
                  setTimeout(() => {
                    setShowSendMe(false)
                    setShowVerse(false)
                  }, 1800)
                }, 1500)
              }
              speechSynthesis.speak(u2)
            }
            speechSynthesis.speak(u1)
          }}
          style={{
            position: 'fixed', inset: 0, zIndex: 300,
            background: 'rgba(0,0,0,0.92)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            gap: 24, cursor: 'pointer',
            opacity: 0,
            animation: 'verseFadeIn 0.5s ease forwards',
          }}
        >
          <p style={{
            fontFamily: 'serif',
            fontSize: '1.1rem',
            color: 'rgba(240,235,224,0.5)',
            textAlign: 'center',
            letterSpacing: 2,
            lineHeight: 1.8,
          }}>
            「そのとき、私は主の御声を聞いた。だれを遣わそうか。」
          </p>
          {!showSendMe && (
            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 11,
              color: 'rgba(201,168,76,0.4)',
              letterSpacing: 3,
              textTransform: 'uppercase',
              animation: 'goldPulse 2s ease infinite',
            }}>
              tap to hear
            </p>
          )}

          {/* SEND ME slam */}
          {showSendMe && (
            <p style={{
              position: 'absolute',
              top: '50%', left: '50%',
              transform: 'translate(-50%,-50%)',
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: '9rem',
              color: '#FFFFFF',
              letterSpacing: 6,
              textTransform: 'uppercase',
              lineHeight: 1,
              textShadow: '0 0 40px rgba(255,255,255,0.3)',
              userSelect: 'none',
            }}>
              SEND ME
            </p>
          )}
        </div>
      )}

      {/* Lightning flash (SEND ME) */}
      {lightningFlash && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 400,
          background: 'rgba(255,255,255,0.85)',
          pointerEvents: 'none',
        }} />
      )}

      {/* Equip flash (per armor piece) */}
      {equipFlash && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 35,
          background: 'rgba(255,255,255,0.5)',
          pointerEvents: 'none',
        }} />
      )}

      {/* UI layer */}
      <div style={{ position: 'relative', zIndex: 10, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopNav currentStep={2} />

        {/* Zen strip */}
        <div style={{
          padding: '8px 24px', textAlign: 'center',
          background: 'rgba(29,158,117,0.06)', borderBottom: '1px solid rgba(29,158,117,0.12)',
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: '#1D9E75', letterSpacing: 2,
        }}>
          &ldquo;Each document is a piece of armor. The warrior dresses for battle one truth at a time.&rdquo;
        </div>

        {/* Main content */}
        <div style={{ flex: 1, display: 'flex' }}>
          {/* Sidebar */}
          <WizardSidebar step={2} accentColor="#1D9E75" mascotSpeech={MASCOT_SPEECH[speechIndex]} />

          {/* Main panel */}
          <div style={{
            flex: 1, padding: '2rem',
            background: 'rgba(4,10,14,0.55)', backdropFilter: 'blur(8px)',
          }}>
            {/* Step header */}
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#1D9E75', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>
              Step 2 of 5 &middot; 水 &middot; The Warrior Dresses
            </p>
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.4rem', color: '#F0EBE0', letterSpacing: 2, marginBottom: 24 }}>
              Upload Your Documents
            </h2>

            {/* Two column grid — warrior left, uploads right */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', alignItems: 'start' }}>

              {/* Left — Armor Warrior */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1rem 0', gap: 16 }}>
                <ArmorWarrior
                  idUploaded={uploads.idUploaded}
                  addressUploaded={uploads.addressUploaded}
                  reportUploaded={uploads.reportUploaded}
                  swordUnsheathed={uploads.swordUnsheathed}
                  pieces={pieces}
                />
                {swordReady && (
                  <p style={{
                    fontFamily: 'var(--font-cinzel), serif',
                    fontSize: 14,
                    color: '#F0D080',
                    textAlign: 'center',
                    textShadow: '0 0 12px rgba(240,208,128,0.3)',
                    letterSpacing: 1.5,
                    lineHeight: 1.6,
                    opacity: 0,
                    animation: 'fadeInGold 1s ease forwards',
                  }}>
                    The warrior is armed.<br />The bureaus have no defense.
                  </p>
                )}
              </div>

              {/* Right — Upload slots */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {/* Slot 1 — Credit Bureau Report → Breastplate */}
                <div style={{
                  padding: '1rem',
                  borderRadius: 5,
                  border: uploads.idUploaded
                    ? '1px solid #1D9E75'
                    : '1px dashed rgba(29,158,117,0.4)',
                  background: uploads.idUploaded ? 'rgba(29,158,117,0.08)' : 'rgba(10,8,6,0.5)',
                  transition: 'all 0.3s',
                }}>
                  <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: '0.78rem', color: '#F0EBE0', letterSpacing: 1, marginBottom: 6 }}>
                    Credit Bureau Report
                  </p>
                  <a
                    href="https://www.annualcreditreport.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#C9A84C', textDecoration: 'none', display: 'inline-block', marginBottom: 10 }}
                  >
                    Free at AnnualCreditReport.gov &#8599;
                  </a>
                  {!uploads.idUploaded ? (
                    <div>
                      <input
                        type="file"
                        accept=".pdf,.txt,.png,.jpg,.jpeg"
                        id="slot1-file"
                        style={{ display: 'none' }}
                        onChange={() => {
                          handleSlotUpload('idUploaded')
                          addPiece('breastplate')
                        }}
                      />
                      <button
                        onClick={() => document.getElementById('slot1-file')?.click()}
                        style={{
                          fontFamily: 'var(--font-body)', fontSize: 12, color: '#1D9E75',
                          background: 'transparent', border: '1px solid rgba(29,158,117,0.3)',
                          padding: '6px 16px', borderRadius: 3, cursor: 'pointer',
                        }}
                      >
                        Choose File
                      </button>
                    </div>
                  ) : (
                    <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#1D9E75' }}>
                      &#10003; Uploaded &mdash; breastplate equipped
                    </p>
                  )}
                </div>

                {/* Slot 2 — Proof of Identity → Leg guards */}
                <ArmorUploadSlot
                  label="Proof of Identity"
                  sublabel="Driver's license · Passport · State ID"
                  armorName="legs"
                  done={uploads.addressUploaded}
                  onComplete={() => {
                    handleSlotUpload('addressUploaded')
                    addPiece('legs')
                  }}
                />

                {/* Slot 3 — Proof of Address → Helmet */}
                <ArmorUploadSlot
                  label="Proof of Address"
                  sublabel="Utility bill · Bank statement"
                  armorName="helmet"
                  done={uploads.reportUploaded}
                  onComplete={() => {
                    handleSlotUpload('reportUploaded')
                    addPiece('helmet')
                  }}
                />

                {/* Sword row */}
                <div style={{
                  padding: '14px 16px',
                  borderRadius: 6,
                  border: uploads.swordUnsheathed
                    ? '1px solid #C9A84C'
                    : uploadCount === 3
                    ? '1px solid rgba(201,168,76,0.5)'
                    : '1px dashed rgba(201,168,76,0.15)',
                  background: uploads.swordUnsheathed ? 'rgba(201,168,76,0.08)' : 'rgba(10,8,6,0.5)',
                  opacity: uploadCount < 3 ? 0.35 : 1,
                  pointerEvents: uploadCount < 3 ? 'none' : 'auto',
                  transition: 'all 0.4s',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <p style={{ fontFamily: 'var(--font-heading)', fontSize: 13, color: '#C9A84C', letterSpacing: 1 }}>
                        刀 Katana — The Blade
                      </p>
                      <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', marginTop: 2 }}>
                        {uploads.swordUnsheathed ? '⚔ The warrior is fully armed.' : 'Upload all 3 documents to unsheathe'}
                      </p>
                    </div>
                    {!uploads.swordUnsheathed && uploadCount === 3 && (
                      <button onClick={handleUnsheathe} style={{
                        fontFamily: 'var(--font-heading)', fontSize: 12, letterSpacing: 2,
                        textTransform: 'uppercase', color: '#050403',
                        background: 'linear-gradient(135deg, #C9A84C, #8B6914)',
                        padding: '8px 18px', borderRadius: 3, border: 'none', cursor: 'pointer',
                      }}>
                        Unsheathe the Sword &rarr;
                      </button>
                    )}
                    {uploads.swordUnsheathed && (
                      <span style={{ fontSize: 20 }}>⚔</span>
                    )}
                  </div>
                </div>

                {/* Continue / Back */}
                <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                  <button onClick={() => navigateTo('/step/1')} style={{
                    fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                    textTransform: 'uppercase', color: '#8A8278', background: 'transparent',
                    padding: '10px 24px', borderRadius: 4, border: '1px solid rgba(138,130,120,0.3)', cursor: 'pointer',
                  }}>
                    &larr; Back
                  </button>
                  <button
                    onClick={() => navigateTo('/step/3')}
                    disabled={!swordReady}
                    style={{
                      fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                      textTransform: 'uppercase', color: '#050403',
                      background: swordReady ? 'linear-gradient(135deg, #C9A84C, #8B6914)' : 'rgba(29,158,117,0.2)',
                      padding: '10px 32px', borderRadius: 4,
                      border: swordReady ? '2px solid #C9A84C' : 'none',
                      cursor: swordReady ? 'pointer' : 'not-allowed',
                      opacity: swordReady ? 1 : 0.5,
                      boxShadow: swordReady ? '0 0 16px rgba(201,168,76,0.3)' : 'none',
                      animation: swordReady ? 'goldPulse 2s ease infinite' : 'none',
                    }}
                  >
                    Continue &rarr;
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Armor Upload Slot with progress states ─── */

function ArmorUploadSlot({ label, sublabel, armorName, done, onComplete }: {
  label: string
  sublabel: string
  armorName: string
  done: boolean
  onComplete: () => void
}) {
  const [status, setStatus] = useState<'pending' | 'uploading' | 'done'>(done ? 'done' : 'pending')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')

  function handleFileSelect(file: File | undefined) {
    if (status !== 'pending' || !file) return
    setStatus('uploading')
    setProgress(0)
    setError('')

    const flask = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'
    const fd = new FormData()
    fd.append('file0', file)
    fd.append('type', armorName)

    const xhr = new XMLHttpRequest()
    xhr.withCredentials = true

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        setProgress(Math.round((e.loaded / e.total) * 100))
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        setProgress(100)
        setTimeout(() => {
          setStatus('done')
          onComplete()
        }, 200)
      } else {
        setError('Upload failed')
        setStatus('pending')
        setProgress(0)
      }
    }

    xhr.onerror = () => {
      setError('Connection failed')
      setStatus('pending')
      setProgress(0)
    }

    xhr.open('POST', `${flask}/api/upload`)
    xhr.send(fd)
  }

  const borderStyle = status === 'done'
    ? '1px solid #1D9E75'
    : status === 'uploading'
    ? '1px solid #1D9E75'
    : '1px dashed rgba(29,158,117,0.4)'

  return (
    <div style={{
      padding: '1rem',
      borderRadius: 5,
      border: borderStyle,
      background: status === 'done' ? 'rgba(29,158,117,0.08)' : 'rgba(10,8,6,0.5)',
      transition: 'all 0.3s',
    }}>
      <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: '0.78rem', color: '#F0EBE0', letterSpacing: 1, marginBottom: 4 }}>
        {label}
      </p>
      <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', marginBottom: 10 }}>
        {sublabel}
      </p>

      {status === 'pending' && (
        <div>
          <input
            type="file"
            accept=".pdf,.txt,.png,.jpg,.jpeg"
            id={`slot-${armorName}`}
            style={{ display: 'none' }}
            onChange={(e) => handleFileSelect(e.target.files?.[0])}
          />
          <button
            onClick={() => document.getElementById(`slot-${armorName}`)?.click()}
            style={{
              fontFamily: 'var(--font-body)', fontSize: 12, color: '#1D9E75',
              background: 'transparent', border: '1px solid rgba(29,158,117,0.3)',
              padding: '6px 16px', borderRadius: 3, cursor: 'pointer',
            }}
          >
            Choose File
          </button>
        </div>
      )}

      {status === 'uploading' && (
        <div>
          <div style={{
            width: '100%', height: 6, background: 'rgba(29,158,117,0.1)',
            borderRadius: 3, overflow: 'hidden', marginBottom: 6,
          }}>
            <div style={{
              width: `${progress}%`, height: '100%',
              background: 'linear-gradient(90deg, #1D9E75, #22A870)',
              borderRadius: 3, transition: 'width 0.15s ease',
            }} />
          </div>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#1D9E75' }}>
            Uploading... {progress}%
          </p>
        </div>
      )}

      {status === 'done' && (
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#1D9E75' }}>
          &#10003; Uploaded &mdash; {armorName} equipped
        </p>
      )}

      {error && (
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#FF4444', marginTop: 4 }}>
          {error}
        </p>
      )}
    </div>
  )
}
