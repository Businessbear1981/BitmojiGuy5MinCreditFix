'use client'

import { useState, useEffect } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { SceneLayout } from '@/components/scene/SceneLayout'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { getLetters } from '@/lib/api'

interface Letter {
  bureau: string
  type: string
  type_label: string
  variant: string
  title: string
  body: string
}

export default function Step3Page() {
  const { navigateTo } = useShojiNav()
  const [letters, setLetters] = useState<Letter[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchLetters() {
      try {
        const res = await getLetters()
        if (res.ok) {
          const data = await res.json()
          setLetters(data.letters || [])
        }
      } catch {
        // Flask may not be running — show empty state
      } finally {
        setLoading(false)
      }
    }
    fetchLetters()
  }, [])

  const displayLetters = letters.slice(0, 4)
  const remaining = Math.max(0, letters.length - 4)

  return (
    <SceneLayout preset="wisdom">
        <TopNav currentStep={3} />

        {/* Zen strip */}
        <div style={{
          padding: '8px 24px', textAlign: 'center',
          background: 'rgba(127,119,221,0.04)', borderBottom: '1px solid rgba(127,119,221,0.1)',
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: '#7F77DD', letterSpacing: 2,
        }}>
          &ldquo;Wisdom is not given. It is earned through ten thousand steps up the mountain.&rdquo;
        </div>

        {/* Main content */}
        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar
            step={3}
            mascotSpeech="The sage climbs every step to earn wisdom. Your 15 letters are aimed with surgical precision."
          />

          {/* Main panel */}
          <div style={{
            flex: 1, padding: '2rem',
            background: 'rgba(8,6,18,0.25)',
          }}>
            {/* Step header */}
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 12, color: '#7F77DD',
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4,
            }}>
              Step 3 of 5 &middot; 智 &middot; The Temple Climb
            </p>
            <h2 style={{
              fontFamily: 'var(--font-heading)', fontSize: '1.4rem', color: '#F0EBE0',
              letterSpacing: 2, marginBottom: 6,
            }}>
              Review Your Letters
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278',
              fontStyle: 'italic', marginBottom: 24,
            }}>
              Each letter is a step up the mountain
            </p>

            {/* Letter grid */}
            {loading ? (
              <div style={{
                padding: '3rem', textAlign: 'center',
                fontFamily: 'var(--font-body)', fontSize: 14, color: '#8A8278',
              }}>
                Loading dispute letters...
              </div>
            ) : displayLetters.length > 0 ? (
              <>
                <div style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14,
                  marginBottom: 16,
                }}>
                  {displayLetters.map((letter, i) => (
                    <LetterCard key={i} letter={letter} />
                  ))}
                </div>

                {remaining > 0 && (
                  <p style={{
                    textAlign: 'center', fontFamily: 'var(--font-body)',
                    fontSize: 13, color: '#7F77DD', opacity: 0.5,
                    letterSpacing: 1, marginBottom: 24,
                  }}>
                    +{remaining} more letters in your package
                  </p>
                )}
              </>
            ) : (
              <div style={{
                padding: '2rem', textAlign: 'center',
                border: '1px dashed rgba(127,119,221,0.2)', borderRadius: 6,
                marginBottom: 24,
              }}>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: '#8A8278' }}>
                  No letters generated yet. Complete Steps 1 &amp; 2 first.
                </p>
              </div>
            )}

            {/* Nav buttons */}
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <button
                onClick={() => navigateTo('/step/2')}
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
                onClick={() => navigateTo('/step/4')}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 14, letterSpacing: 3,
                  textTransform: 'uppercase', color: '#050403',
                  background: 'linear-gradient(135deg, #7F77DD, #4A4499)',
                  padding: '12px 40px', borderRadius: 4, border: 'none',
                  cursor: 'pointer',
                  boxShadow: '0 4px 20px rgba(127,119,221,0.3)',
                }}
              >
                Continue &rarr;
              </button>
            </div>
          </div>
        </div>
    </SceneLayout>
  )
}

/* ─── Letter Card ─── */

function LetterCard({ letter }: { letter: Letter }) {
  const [hovered, setHovered] = useState(false)

  // Extract FCRA citation from body
  let statute = 'FCRA Section 611'
  if (letter.body.includes('809(b)')) statute = 'FDCPA 809(b) · FCRA 611'
  else if (letter.body.includes('605(a)')) statute = 'FCRA 605(a)'
  else if (letter.body.includes('605B')) statute = 'FCRA 605B'
  else if (letter.body.includes('611(a)(6)')) statute = 'FCRA 611(a)(6)(B)(iii)'
  else if (letter.body.includes('605(c)')) statute = 'FCRA 605(c)'
  else if (letter.body.includes('623')) statute = 'FCRA 623(a)(1)(F)'

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'rgba(0,0,0,0.35)',
        border: `1px solid ${hovered ? '#7F77DD' : 'rgba(127,119,221,0.2)'}`,
        borderRadius: 6,
        padding: '16px 18px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        boxShadow: hovered ? '0 0 16px rgba(127,119,221,0.1)' : 'none',
      }}
    >
      {/* Type tag */}
      <span style={{
        fontFamily: 'var(--font-body)', fontSize: 10, letterSpacing: 1.5,
        textTransform: 'uppercase', color: '#7F77DD',
        padding: '2px 8px', borderRadius: 3,
        border: '1px solid rgba(127,119,221,0.25)',
        display: 'inline-block', marginBottom: 8,
      }}>
        {letter.type_label} &middot; {letter.variant}
      </span>

      {/* Letter name */}
      <p style={{
        fontFamily: 'var(--font-heading)', fontSize: '0.82rem', color: '#F0EBE0',
        letterSpacing: 1, marginBottom: 6, lineHeight: 1.3,
      }}>
        {letter.title}
      </p>

      {/* Bureau + statute */}
      <p style={{
        fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
        letterSpacing: 0.5,
      }}>
        {letter.bureau} &middot; {statute}
      </p>
    </div>
  )
}
