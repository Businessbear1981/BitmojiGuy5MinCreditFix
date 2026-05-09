'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { useWizardStore } from '@/store/wizardStore'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { ArmorWarrior } from '@/components/warrior/ArmorWarrior'
import { uploadDocument, parseReportServer } from '@/lib/api'

const ACCENT = '#C9A84C'

type DocType = 'id' | 'address' | 'report'

interface SlotState {
  armored: boolean
  filename: string
  sizeKb: number
  uploading: boolean
  progress: number
  error: string
  previewUrl: string
}

interface SlotConfig {
  key: DocType
  kanji: string
  armor: string
  title: string
  subtitle: string
  hint: string
  link?: string
  accept: string
}

const SLOTS: SlotConfig[] = [
  {
    key: 'id', kanji: '面', armor: 'Helm', title: 'Photo ID',
    subtitle: 'Government-issued identification',
    hint: 'Driver license, passport, or state ID',
    accept: '.pdf,.png,.jpg,.jpeg',
  },
  {
    key: 'address', kanji: '鎧', armor: 'Breastplate', title: 'Proof of Address',
    subtitle: 'Current residential address verification',
    hint: 'Utility bill, bank statement, or lease agreement',
    accept: '.pdf,.png,.jpg,.jpeg,.docx',
  },
  {
    key: 'report', kanji: '剣', armor: 'Sword', title: 'Credit Report',
    subtitle: 'Full report from any bureau',
    hint: 'Get yours free at annualcreditreport.com — PDF, Word, HTML, or text',
    link: 'https://www.annualcreditreport.com',
    accept: '.pdf,.txt,.csv,.html,.htm,.docx,.doc,.odt,.rtf,.xml',
  },
]

const MAX_FILE_SIZE = 25 * 1024 * 1024

export default function DojoPage() {
  const { navigateTo } = useShojiNav()
  const { uploads, setUpload, formData, setDisputeItems, setReportRawText } = useWizardStore()
  const [slots, setSlots] = useState<Record<DocType, SlotState>>({
    id:      { armored: uploads.idUploaded,      filename: '', sizeKb: 0, uploading: false, progress: 0, error: '', previewUrl: '' },
    address: { armored: uploads.addressUploaded, filename: '', sizeKb: 0, uploading: false, progress: 0, error: '', previewUrl: '' },
    report:  { armored: uploads.reportUploaded,  filename: '', sizeKb: 0, uploading: false, progress: 0, error: '', previewUrl: '' },
  })
  const [unlockAnim, setUnlockAnim] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<{ count: number; categories: string[] } | null>(null)

  const allArmored = slots.id.armored && slots.address.armored && slots.report.armored
  const armoredCount = [slots.id.armored, slots.address.armored, slots.report.armored].filter(Boolean).length

  // Sword unsheathe
  useEffect(() => {
    if (allArmored && !uploads.swordUnsheathed) {
      setUpload('swordUnsheathed', true)
      // Cinematic unlock delay
      setTimeout(() => setUnlockAnim(true), 800)
    }
  }, [allArmored, uploads.swordUnsheathed, setUpload])

  const handleFile = useCallback(async (key: DocType, file: File) => {
    // Size check
    if (file.size > MAX_FILE_SIZE) {
      setSlots((s) => ({ ...s, [key]: { ...s[key], error: `File too large (${formatSize(file.size)}). Max 25MB.` } }))
      return
    }

    // Generate preview for images
    let previewUrl = ''
    if (file.type.startsWith('image/')) {
      previewUrl = URL.createObjectURL(file)
    }

    // Start upload with simulated progress
    setSlots((s) => ({
      ...s,
      [key]: { ...s[key], uploading: true, progress: 0, error: '', filename: file.name, sizeKb: Math.round(file.size / 1024), previewUrl },
    }))

    // Simulate progress ticks while upload runs
    const progressInterval = setInterval(() => {
      setSlots((s) => {
        const current = s[key].progress
        if (current >= 90) return s
        return { ...s, [key]: { ...s[key], progress: current + Math.random() * 15 } }
      })
    }, 200)

    try {
      // If credit report — send to Flask parser (pdfplumber + BeautifulSoup + regex)
      if (key === 'report') {
        setAnalyzing(true)
        setAnalysisResult(null)
        const parseRes = await parseReportServer(file, formData.state || 'TX')
        const parseData = await parseRes.json()
        if (parseData.ok && parseData.dispute_items?.length > 0) {
          setDisputeItems(parseData.dispute_items)
          const categories = [...new Set(parseData.dispute_items.map((i: { dispute_label?: string; label?: string }) => i.dispute_label || i.label).filter(Boolean))] as string[]
          setAnalysisResult({ count: parseData.dispute_items.length, categories })
          await new Promise((r) => setTimeout(r, 2000))
        } else {
          setAnalysisResult({ count: 0, categories: [] })
          await new Promise((r) => setTimeout(r, 1500))
        }
        setAnalyzing(false)
      } else {
        // ID and address — just send to Flask in background
        uploadDocument(file, key).catch(() => {})
      }

      clearInterval(progressInterval)

      // Complete — snap to 100%
      setSlots((s) => ({ ...s, [key]: { ...s[key], progress: 100 } }))

      // Brief pause at 100% then mark armored
      await new Promise((r) => setTimeout(r, 400))
      setSlots((s) => ({ ...s, [key]: { ...s[key], uploading: false, armored: true, error: '' } }))
      setUpload(`${key}Uploaded` as 'idUploaded' | 'addressUploaded' | 'reportUploaded', true)
    } catch (e) {
      clearInterval(progressInterval)
      setSlots((s) => ({
        ...s,
        [key]: { ...s[key], uploading: false, progress: 0, armored: false, error: e instanceof Error ? e.message : 'Could not connect to server.' },
      }))
    }
  }, [setUpload])

  return (
    <>
      {/* Background */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/dojo.png"
        alt=""
        style={{
          position: 'fixed', top: 0, left: 0,
          width: '100vw', height: '100vh',
          objectFit: 'cover', zIndex: 0,
        }}
      />

      <div style={{ position: 'relative', zIndex: 2, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopNav currentStep={2} />

        {/* Quote bar */}
        <div style={{
          padding: '10px 24px', textAlign: 'center',
          background: `${ACCENT}0A`, borderBottom: `1px solid ${ACCENT}22`,
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: ACCENT, letterSpacing: 2,
          textShadow: `0 0 8px currentColor, 0 0 20px currentColor`,
        }}>
          &ldquo;Three pieces of armor. Each one earned by an upload. The warrior must be complete.&rdquo;
        </div>

        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar step={2} mascotSpeech="Three uploads. Three pieces of armor. Helm, breastplate, sword. Then we march." />

          <div style={{ flex: 1, padding: '2rem', background: 'rgba(14,10,4,0.25)' }}>
            <div style={{ maxWidth: 900, margin: '0 auto' }}>
              {/* Header */}
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT,
                letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4,
                textShadow: `0 0 8px currentColor, 0 0 20px currentColor`,
              }}>
                Step 2 of 7 &middot; 武 &middot; The Dojo
              </p>
              <h2 style={{
                fontFamily: 'var(--font-cinzel-decorative), serif',
                fontSize: '1.8rem', color: '#F0EBE0', letterSpacing: 2,
                marginTop: 0, marginBottom: 6,
                textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 24px ${ACCENT}55`,
              }}>
                THE DOJO &mdash; FORGE YOUR ARMOR
              </h2>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278',
                fontStyle: 'italic', marginBottom: 24,
              }}>
                Each document forges a piece of armor. Upload all three to arm the warrior.
              </p>

              {/* ═══ MAIN GRID: Warrior left, Uploads right ═══ */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '260px 1fr',
                gap: 32,
                alignItems: 'start',
                marginBottom: 32,
              }}>
                {/* Warrior column */}
                <div style={{
                  position: 'sticky', top: 80,
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  padding: '16px 0',
                }}>
                  <ArmorWarrior
                    idUploaded={slots.id.armored}
                    addressUploaded={slots.address.armored}
                    reportUploaded={slots.report.armored}
                    swordUnsheathed={allArmored}
                  />
                </div>

                {/* Upload slots column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* Progress banner */}
                  <div style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '14px 18px',
                    background: `${ACCENT}11`, borderLeft: `3px solid ${ACCENT}`,
                    borderRadius: 4,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      {/* Mini progress dots */}
                      {[slots.id.armored, slots.address.armored, slots.report.armored].map((done, i) => (
                        <div key={i} style={{
                          width: 10, height: 10, borderRadius: '50%',
                          background: done ? ACCENT : 'rgba(138,130,120,0.3)',
                          boxShadow: done ? `0 0 8px ${ACCENT}88` : 'none',
                          transition: 'all 0.4s',
                        }} />
                      ))}
                      <span style={{
                        fontFamily: 'var(--font-cinzel), serif', fontSize: 13,
                        color: ACCENT, letterSpacing: 2, textTransform: 'uppercase',
                        textShadow: `0 0 8px currentColor, 0 0 20px currentColor`,
                      }}>
                        Armor: {armoredCount} of 3
                      </span>
                    </div>
                    <span style={{
                      fontFamily: 'var(--font-body)', fontSize: 11,
                      color: allArmored ? ACCENT : '#8A8278',
                      textShadow: allArmored ? `0 0 8px ${ACCENT}88` : 'none',
                    }}>
                      {allArmored ? '\u2694 Sword unsheathed' : 'Continue locked'}
                    </span>
                  </div>

                  {/* Upload cards */}
                  {SLOTS.map((cfg) => (
                    <UploadCard
                      key={cfg.key}
                      cfg={cfg}
                      state={slots[cfg.key]}
                      onFile={(f) => handleFile(cfg.key, f)}
                    />
                  ))}
                </div>
              </div>

              {/* ═══ NAVIGATION ═══ */}
              <div style={{
                display: 'flex', gap: 12, justifyContent: 'space-between',
                paddingTop: 8,
                borderTop: '1px solid rgba(201,168,76,0.1)',
              }}>
                <button
                  onClick={() => navigateTo('/map')}
                  style={{
                    fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                    textTransform: 'uppercase', color: '#8A8278', background: 'transparent',
                    padding: '12px 28px', borderRadius: 4,
                    border: '1px solid rgba(138,130,120,0.3)', cursor: 'pointer',
                    textShadow: `0 0 8px currentColor, 0 0 20px currentColor`,
                  }}
                >
                  &larr; Back
                </button>
                <button
                  onClick={() => navigateTo('/koi-pond')}
                  disabled={!allArmored}
                  style={{
                    fontFamily: 'var(--font-heading)', fontSize: 15, fontWeight: 700,
                    letterSpacing: 3, textTransform: 'uppercase',
                    color: allArmored ? '#050403' : '#8A8278',
                    background: allArmored
                      ? `linear-gradient(135deg, ${ACCENT}, #8B6914)`
                      : 'rgba(100,100,100,0.2)',
                    padding: '14px 48px', borderRadius: 4,
                    border: allArmored ? '1px solid #8B5A20' : '1px solid rgba(138,130,120,0.2)',
                    cursor: allArmored ? 'pointer' : 'not-allowed',
                    boxShadow: allArmored ? `0 6px 30px ${ACCENT}55, inset 0 1px 0 rgba(255,255,255,0.2)` : 'none',
                    opacity: allArmored ? 1 : 0.4,
                    transform: unlockAnim ? 'scale(1)' : (allArmored ? 'scale(1.05)' : 'scale(1)'),
                    transition: 'all 0.6s ease',
                    animation: unlockAnim ? 'unlockPulse 1.5s ease' : undefined,
                  }}
                >
                  {allArmored ? 'March to the Koi Pond \u2192' : 'Forge all 3 to continue'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ═══ ANALYSIS OVERLAY ═══ */}
      {(analyzing || analysisResult) && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            maxWidth: 480, width: '100%', padding: '3rem 2.5rem',
            background: 'rgba(14,10,4,0.95)', border: `1px solid ${ACCENT}44`,
            borderRadius: 12, textAlign: 'center',
            boxShadow: `0 0 60px ${ACCENT}22`,
          }}>
            {analysisResult ? (
              <>
                <div style={{
                  fontFamily: 'serif', fontSize: 48, color: ACCENT,
                  marginBottom: 16,
                  textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 40px ${ACCENT}44`,
                }}>
                  剣
                </div>
                <h3 style={{
                  fontFamily: 'var(--font-cinzel-decorative), serif',
                  fontSize: '1.4rem', color: '#F0EBE0', letterSpacing: 2,
                  marginBottom: 8,
                  textShadow: '0 0 8px currentColor, 0 0 20px currentColor',
                }}>
                  Report Analyzed
                </h3>
                <p style={{
                  fontFamily: 'var(--font-cinzel), serif',
                  fontSize: '2rem', color: ACCENT, letterSpacing: 3,
                  marginBottom: 12,
                  textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 30px ${ACCENT}66`,
                }}>
                  {analysisResult.count} Dispute{analysisResult.count !== 1 ? 's' : ''} Found
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginBottom: 16 }}>
                  {analysisResult.categories.map((cat) => (
                    <span key={cat} style={{
                      fontFamily: 'var(--font-body)', fontSize: 10, letterSpacing: 1.5,
                      textTransform: 'uppercase', color: ACCENT,
                      padding: '4px 10px', borderRadius: 3,
                      border: `1px solid ${ACCENT}44`, background: `${ACCENT}11`,
                    }}>
                      {cat}
                    </span>
                  ))}
                </div>
                <button
                  onClick={() => setAnalysisResult(null)}
                  style={{
                    marginTop: 8,
                    fontFamily: 'var(--font-heading)', fontSize: 14, fontWeight: 700,
                    letterSpacing: 3, textTransform: 'uppercase',
                    color: '#050403',
                    background: `linear-gradient(135deg, ${ACCENT}, #8B6914)`,
                    padding: '14px 48px', borderRadius: 4,
                    border: '1px solid #8B5A20', cursor: 'pointer',
                    boxShadow: `0 6px 30px ${ACCENT}55, inset 0 1px 0 rgba(255,255,255,0.2)`,
                    textShadow: 'none',
                  }}
                >
                  Continue \u2192
                </button>
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
                  fontStyle: 'italic', marginTop: 8,
                }}>
                  Authorize disputes on the next screen
                </p>
              </>
            ) : (
              <>
                <div style={{
                  fontFamily: 'serif', fontSize: 48, color: ACCENT,
                  marginBottom: 16,
                  animation: 'analysisPulse 1.5s ease-in-out infinite',
                  textShadow: `0 0 8px currentColor, 0 0 20px currentColor`,
                }}>
                  剣
                </div>
                <h3 style={{
                  fontFamily: 'var(--font-cinzel-decorative), serif',
                  fontSize: '1.2rem', color: '#F0EBE0', letterSpacing: 2,
                  marginBottom: 8,
                  textShadow: '0 0 8px currentColor, 0 0 20px currentColor',
                }}>
                  Analyzing Credit Report...
                </h3>
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 12, color: '#8A8278',
                }}>
                  Scanning for collections, late payments, incorrect addresses, unknown accounts, and aged debt
                </p>
                <div style={{
                  marginTop: 20, height: 3, background: 'rgba(255,255,255,0.06)',
                  borderRadius: 2, overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%', width: '60%',
                    background: `linear-gradient(90deg, transparent, ${ACCENT}, transparent)`,
                    animation: 'analysisScan 1.5s ease-in-out infinite',
                  }} />
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <style>{`
        @keyframes analysisPulse {
          0%, 100% { opacity: 0.6; transform: scale(1); }
          50%      { opacity: 1; transform: scale(1.1); }
        }
        @keyframes analysisScan {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        @keyframes unlockPulse {
          0%   { transform: scale(1); box-shadow: 0 6px 30px ${ACCENT}55; }
          30%  { transform: scale(1.08); box-shadow: 0 6px 40px ${ACCENT}88, 0 0 60px ${ACCENT}44; }
          60%  { transform: scale(1.02); }
          100% { transform: scale(1); box-shadow: 0 6px 30px ${ACCENT}55; }
        }
      `}</style>
    </>
  )
}

/* ═══════════════════════════════════════════════════════
   UPLOAD CARD — full-featured upload slot
   ═══════════════════════════════════════════════════════ */

function UploadCard({ cfg, state, onFile }: {
  cfg: SlotConfig
  state: SlotState
  onFile: (f: File) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)

  function pick() { inputRef.current?.click() }

  const borderColor = state.armored
    ? `${ACCENT}88`
    : drag
    ? `${ACCENT}66`
    : 'rgba(138,130,120,0.2)'

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault(); setDrag(false)
        const f = e.dataTransfer.files?.[0]
        if (f) onFile(f)
      }}
      style={{
        padding: '20px',
        background: state.armored
          ? `linear-gradient(135deg, ${ACCENT}12, rgba(0,0,0,0.3))`
          : drag
          ? `${ACCENT}0A`
          : 'rgba(0,0,0,0.4)',
        border: `1px solid ${borderColor}`,
        borderRadius: 8,
        transition: 'all 0.3s ease',
        boxShadow: state.armored ? `0 0 20px ${ACCENT}22` : 'none',
      }}
    >
      {/* Top row: badge + info + action */}
      <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr auto', alignItems: 'center', gap: 16 }}>
        {/* Armor badge */}
        <div style={{
          width: 56, height: 56, borderRadius: 8,
          border: `2px solid ${state.armored ? ACCENT : '#5A5A5A'}`,
          background: state.armored
            ? `linear-gradient(135deg, ${ACCENT}33, ${ACCENT}11)`
            : 'rgba(0,0,0,0.6)',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          boxShadow: state.armored ? `0 0 16px ${ACCENT}66, inset 0 0 8px ${ACCENT}22` : 'none',
          transition: 'all 0.5s ease',
        }}>
          <span style={{
            fontFamily: 'serif', fontSize: 22,
            color: state.armored ? ACCENT : '#8A8278',
            lineHeight: 1,
            textShadow: state.armored ? `0 0 8px ${ACCENT}88` : 'none',
          }}>
            {state.armored ? '\u2713' : cfg.kanji}
          </span>
          <span style={{
            fontFamily: 'var(--font-cinzel), serif', fontSize: 7,
            color: state.armored ? ACCENT : '#8A8278',
            letterSpacing: 1.5, textTransform: 'uppercase', marginTop: 2,
          }}>
            {cfg.armor}
          </span>
        </div>

        {/* Info */}
        <div>
          <p style={{
            fontFamily: 'var(--font-heading)', fontSize: 15, color: '#F0EBE0',
            letterSpacing: 0.5, margin: 0, marginBottom: 2,
            textShadow: '0 0 8px currentColor, 0 0 20px currentColor',
          }}>
            {cfg.title}
          </p>
          <p style={{
            fontFamily: 'var(--font-body)', fontSize: 11, color: '#A8A29A',
            margin: 0, marginBottom: 2,
          }}>
            {cfg.subtitle}
          </p>

          {state.armored ? (
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: ACCENT, margin: 0 }}>
              \u2713 {state.filename} <span style={{ color: '#8A8278' }}>&middot; {formatSize(state.sizeKb * 1024)}</span>
            </p>
          ) : state.uploading ? (
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: ACCENT, margin: 0, fontStyle: 'italic' }}>
              Forging {cfg.armor.toLowerCase()}... {Math.round(state.progress)}%
            </p>
          ) : (
            <div>
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 10, color: '#8A8278', margin: 0 }}>
                {cfg.hint}
              </p>
              {cfg.link && (
                <a
                  href={cfg.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontFamily: 'var(--font-body)', fontSize: 10,
                    color: ACCENT, textDecoration: 'underline',
                    textShadow: `0 0 8px currentColor, 0 0 20px currentColor`,
                  }}
                >
                  annualcreditreport.com &rarr;
                </a>
              )}
            </div>
          )}
        </div>

        {/* Action button */}
        <div>
          <input
            ref={inputRef}
            type="file"
            accept={cfg.accept}
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) onFile(f)
              e.target.value = ''
            }}
            style={{ display: 'none' }}
          />
          <button
            onClick={pick}
            disabled={state.uploading}
            style={{
              fontFamily: 'var(--font-heading)', fontSize: 12, letterSpacing: 2,
              textTransform: 'uppercase',
              color: state.armored ? ACCENT : '#F0EBE0',
              background: state.armored
                ? 'transparent'
                : `linear-gradient(135deg, ${ACCENT}, #8B6914)`,
              padding: '10px 20px', borderRadius: 4,
              border: state.armored ? `1px solid ${ACCENT}66` : 'none',
              cursor: state.uploading ? 'wait' : 'pointer',
              boxShadow: state.armored ? 'none' : `0 2px 12px ${ACCENT}44`,
              transition: 'all 0.3s',
              textShadow: '0 0 8px currentColor, 0 0 20px currentColor',
            }}
          >
            {state.armored ? 'Replace' : state.uploading ? 'Forging...' : 'Upload'}
          </button>
        </div>
      </div>

      {/* Progress bar */}
      {state.uploading && (
        <div style={{
          marginTop: 14, height: 4,
          background: 'rgba(255,255,255,0.06)',
          borderRadius: 2, overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${Math.min(state.progress, 100)}%`,
            background: `linear-gradient(90deg, ${ACCENT}, #F0D080)`,
            borderRadius: 2,
            boxShadow: `0 0 8px ${ACCENT}88`,
            transition: 'width 0.3s ease',
          }} />
        </div>
      )}

      {/* File preview (images only) */}
      {state.previewUrl && state.armored && (
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={state.previewUrl}
            alt="Preview"
            style={{
              width: 48, height: 48, objectFit: 'cover',
              borderRadius: 4, border: `1px solid ${ACCENT}44`,
            }}
          />
          <span style={{ fontFamily: 'var(--font-body)', fontSize: 10, color: '#8A8278' }}>
            Preview attached
          </span>
        </div>
      )}

      {/* Error */}
      {state.error && (
        <div style={{
          marginTop: 10, padding: '8px 12px',
          background: 'rgba(255,60,60,0.1)', border: '1px solid rgba(255,60,60,0.3)',
          borderRadius: 4,
        }}>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#FF6B6B', margin: 0 }}>
            {state.error}
          </p>
        </div>
      )}

      {/* Drag overlay */}
      {drag && !state.uploading && (
        <div style={{
          marginTop: 10, padding: '16px',
          border: `2px dashed ${ACCENT}66`,
          borderRadius: 6,
          textAlign: 'center',
          background: `${ACCENT}08`,
        }}>
          <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 12, color: ACCENT, margin: 0, letterSpacing: 2 }}>
            Drop file here
          </p>
        </div>
      )}
    </div>
  )
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
