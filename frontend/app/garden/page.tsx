'use client'

import { useState, useEffect } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { getLetters, getLetterById } from '@/lib/api'

const ACCENT = '#EF9F27'

interface Letter {
  bureau: string
  type_label: string
  variant: string
  title: string
}

interface LetterDetail {
  bureau: string
  bureau_full_address: { name?: string; address?: string; city?: string; state?: string; zip?: string }
  type_label: string
  variant: string
  title: string
  body: string
  client_name: string
  client_address: string
  confirmation: string
}

export default function GardenPage() {
  const { navigateTo } = useShojiNav()
  const [letters, setLetters] = useState<Letter[]>([])
  const [fetchedOk, setFetchedOk] = useState(false)
  const [generating, setGenerating] = useState(true)
  const [progress, setProgress] = useState(0)
  const [modalLetter, setModalLetter] = useState<LetterDetail | null>(null)
  const [loadingLetter, setLoadingLetter] = useState(false)

  async function openLetter(index: number) {
    setLoadingLetter(true)
    try {
      const res = await getLetterById(index)
      if (res.ok) {
        const data = await res.json()
        setModalLetter(data.letter)
      }
    } catch { /* Flask not running */ }
    setLoadingLetter(false)
  }

  // Fetch the real letters
  useEffect(() => {
    (async () => {
      try {
        const res = await getLetters()
        if (res.ok) {
          const data = await res.json()
          setLetters(data.letters || [])
          setFetchedOk(true)
        }
      } catch {
        // Flask not running
      }
    })()
  }, [])

  // Rake animation — counts 0 → 15
  useEffect(() => {
    if (!generating) return
    const target = letters.length > 0 ? letters.length : 15
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= target) {
          clearInterval(interval)
          setTimeout(() => setGenerating(false), 400)
          return target
        }
        return p + 1
      })
    }, 120)
    return () => clearInterval(interval)
  }, [generating, letters.length])

  const total = letters.length > 0 ? letters.length : 15

  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/garden.webp"
        alt=""
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          objectFit: 'cover',
          zIndex: 0,
        }}
      />

      <div style={{ position: 'relative', zIndex: 10, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopNav currentStep={4} />

        <div style={{
          padding: '8px 24px', textAlign: 'center',
          background: `${ACCENT}0A`, borderBottom: `1px solid ${ACCENT}22`,
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: ACCENT, letterSpacing: 2,
          textShadow: `0 0 12px ${ACCENT}88, 0 0 24px ${ACCENT}44`,
        }}>
          &ldquo;Rake the sand. Each line is a letter. Each letter is a vow.&rdquo;
        </div>

        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar
            step={4}
            mascotSpeech="The monk rakes the sand. Fifteen lines. Fifteen letters. Each one aimed at a bureau."
          />

          <div style={{
            flex: 1, padding: '2rem',
            background: 'rgba(14,10,4,0.2)',
            display: 'flex', flexDirection: 'column', alignItems: 'center',
          }}>
          <div style={{ width: '100%', maxWidth: 720 }}>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT,
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4,
            }}>
              Step 4 of 7 &middot; 庭 &middot; The Sand Garden
            </p>
            <h2 style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: '1.6rem', color: '#F0EBE0', letterSpacing: 2,
              marginTop: 0, marginBottom: 6,
              textShadow: `0 0 24px ${ACCENT}55`,
            }}>
              Generate Your Letters
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278',
              fontStyle: 'italic', marginBottom: 24,
            }}>
              Fifteen bureau-aimed letters &middot; FCRA, FDCPA, state citations woven in
            </p>

            {/* Rake-progress — during generation */}
            {generating && (
              <div style={{
                padding: '2.5rem 1.5rem',
                border: `1px solid ${ACCENT}33`,
                borderRadius: 8,
                background: 'rgba(0,0,0,0.4)',
                marginBottom: 20,
              }}>
                {/* Raked-sand lines */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 20 }}>
                  {Array.from({ length: total }).map((_, i) => (
                    <div key={i} style={{
                      height: 3, borderRadius: 2,
                      background: i < progress ? `linear-gradient(90deg, ${ACCENT}, ${ACCENT}88, transparent)` : 'rgba(255,255,255,0.04)',
                      boxShadow: i < progress ? `0 0 8px ${ACCENT}55` : 'none',
                      transition: 'background 0.25s, box-shadow 0.25s',
                    }} />
                  ))}
                </div>

                <p style={{
                  textAlign: 'center',
                  fontFamily: 'var(--font-cinzel), serif', fontSize: 13,
                  color: ACCENT, letterSpacing: 3, textTransform: 'uppercase',
                }}>
                  Raking {progress} of {total}
                </p>
              </div>
            )}

            {/* Grid of letters — after generation */}
            {!generating && (
              <>
                <div style={{
                  display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10,
                  marginBottom: 20,
                }}>
                  {(fetchedOk && letters.length > 0 ? letters : Array.from({ length: 15 }).map((_, i) => ({
                    bureau: ['Equifax', 'TransUnion', 'Experian'][i % 3],
                    type_label: ['Collections', 'Late Pay', 'Identity', 'Obsolete', 'Inquiry'][i % 5],
                    variant: 'A',
                    title: `Dispute Letter #${i + 1}`,
                  }))).map((l, i) => (
                    <div key={i} style={{
                      background: 'rgba(0,0,0,0.4)',
                      border: `1px solid ${ACCENT}33`,
                      borderRadius: 4,
                      padding: '10px 12px',
                      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                    }}>
                      <div>
                        <p style={{
                          fontFamily: 'var(--font-body)', fontSize: 9, letterSpacing: 1.5,
                          textTransform: 'uppercase', color: ACCENT, marginBottom: 4,
                        }}>
                          {l.bureau} &middot; {l.type_label}
                        </p>
                        <p style={{
                          fontFamily: 'var(--font-heading)', fontSize: 11, color: '#F0EBE0',
                          lineHeight: 1.3, marginBottom: 8,
                        }}>
                          {l.title}
                        </p>
                      </div>
                      <button
                        onClick={() => openLetter(i)}
                        disabled={loadingLetter}
                        style={{
                          fontFamily: 'var(--font-body)', fontSize: 10, letterSpacing: 1,
                          textTransform: 'uppercase', color: ACCENT,
                          background: `${ACCENT}15`,
                          border: `1px solid ${ACCENT}44`,
                          borderRadius: 3, padding: '5px 0',
                          cursor: 'pointer',
                          transition: 'background 0.2s',
                        }}
                      >
                        View Letter
                      </button>
                    </div>
                  ))}
                </div>

                <div style={{
                  padding: '12px 16px',
                  background: `${ACCENT}11`, borderLeft: `3px solid ${ACCENT}`,
                  borderRadius: 4, marginBottom: 24,
                }}>
                  <p style={{
                    fontFamily: 'var(--font-cinzel), serif', fontSize: 11,
                    color: ACCENT, letterSpacing: 2, textTransform: 'uppercase',
                    marginBottom: 2,
                  }}>
                    {total} letters generated &middot; ready for dispatch
                  </p>
                  <p style={{
                    fontFamily: 'var(--font-body)', fontSize: 11, color: '#A8A29A',
                    lineHeight: 1.5, margin: 0,
                  }}>
                    {fetchedOk ? 'Letters loaded from backend.' : 'Demo preview — backend not connected.'} Pay to unlock and dispatch.
                  </p>
                </div>
              </>
            )}

            <div style={{ display: 'flex', gap: 12, justifyContent: 'space-between' }}>
              <button
                onClick={() => navigateTo('/koi-pond')}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: '#8A8278', background: 'transparent',
                  padding: '10px 24px', borderRadius: 4,
                  border: '1px solid rgba(138,130,120,0.3)', cursor: 'pointer',
                }}
              >
                &larr; Back
              </button>
              <button
                onClick={() => navigateTo('/stairway')}
                disabled={generating}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 14, letterSpacing: 3,
                  textTransform: 'uppercase', color: '#050403',
                  background: generating
                    ? 'rgba(100,100,100,0.3)'
                    : `linear-gradient(135deg, ${ACCENT}, #A06810)`,
                  padding: '12px 40px', borderRadius: 4, border: 'none',
                  cursor: generating ? 'not-allowed' : 'pointer',
                  boxShadow: generating ? 'none' : `0 4px 20px ${ACCENT}55`,
                  opacity: generating ? 0.5 : 1,
                }}
              >
                {generating ? 'Generating...' : 'Continue to Toll →'}
              </button>
            </div>
          </div>
        </div>
      </div>
      </div>

      {/* Letter Preview Modal */}
      {modalLetter && (
        <div
          onClick={() => setModalLetter(null)}
          style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(6px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: 24,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '100%', maxWidth: 640, maxHeight: '85vh',
              background: '#0E0A04', border: `1px solid ${ACCENT}44`,
              borderRadius: 8, overflow: 'auto',
              boxShadow: `0 0 60px ${ACCENT}22`,
            }}
          >
            {/* Modal header */}
            <div style={{
              padding: '16px 20px', borderBottom: `1px solid ${ACCENT}22`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              position: 'sticky', top: 0, background: '#0E0A04', zIndex: 1,
            }}>
              <div>
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 10, letterSpacing: 1.5,
                  textTransform: 'uppercase', color: ACCENT, margin: 0,
                }}>
                  {modalLetter.bureau} &middot; {modalLetter.type_label} &middot; Variant {modalLetter.variant}
                </p>
                <p style={{
                  fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '1.1rem',
                  color: '#F0EBE0', margin: '4px 0 0',
                }}>
                  {modalLetter.title}
                </p>
              </div>
              <button
                onClick={() => setModalLetter(null)}
                style={{
                  background: 'none', border: 'none', color: '#8A8278',
                  fontSize: 22, cursor: 'pointer', padding: '4px 8px',
                }}
              >
                &times;
              </button>
            </div>

            {/* Bureau address block */}
            {modalLetter.bureau_full_address && (
              <div style={{
                padding: '14px 20px', borderBottom: `1px solid ${ACCENT}11`,
                fontFamily: 'var(--font-body)', fontSize: 12, color: '#A8A29A',
                lineHeight: 1.6,
              }}>
                <p style={{ margin: 0, color: ACCENT, fontWeight: 600 }}>TO:</p>
                <p style={{ margin: '2px 0 0' }}>
                  {modalLetter.bureau_full_address.name}<br />
                  {modalLetter.bureau_full_address.address}<br />
                  {modalLetter.bureau_full_address.city}, {modalLetter.bureau_full_address.state} {modalLetter.bureau_full_address.zip}
                </p>
              </div>
            )}

            {/* From block */}
            {modalLetter.client_name && (
              <div style={{
                padding: '10px 20px', borderBottom: `1px solid ${ACCENT}11`,
                fontFamily: 'var(--font-body)', fontSize: 12, color: '#A8A29A',
                lineHeight: 1.6,
              }}>
                <p style={{ margin: 0, color: ACCENT, fontWeight: 600 }}>FROM:</p>
                <p style={{ margin: '2px 0 0' }}>
                  {modalLetter.client_name}
                  {modalLetter.client_address && <><br />{modalLetter.client_address}</>}
                  {modalLetter.confirmation && (
                    <><br /><span style={{ color: ACCENT }}>Ref: {modalLetter.confirmation}</span></>
                  )}
                </p>
              </div>
            )}

            {/* Letter body */}
            <div style={{
              padding: '20px',
              fontFamily: 'var(--font-body)', fontSize: 13, color: '#E0DCD4',
              lineHeight: 1.8, whiteSpace: 'pre-wrap',
            }}>
              {modalLetter.body}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
