'use client'

import { useState } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { SceneLayout } from '@/components/scene/SceneLayout'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'

export default function Step5Page() {
  const { navigateTo } = useShojiNav()
  const [mailClass, setMailClass] = useState<'first' | 'certified'>('certified')
  const [sending, setSending] = useState(false)
  const [mailResult, setMailResult] = useState('')

  return (
    <SceneLayout preset="nirvana">
        <TopNav currentStep={5} />

        {/* Zen strip */}
        <div style={{
          padding: '8px 24px', textAlign: 'center',
          background: 'rgba(93,202,165,0.04)', borderBottom: '1px solid rgba(93,202,165,0.1)',
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: '#5CFFCC', letterSpacing: 2,
        }}>
          &ldquo;The petals fall through the gate. The journey is complete. Breathe.&rdquo;
        </div>

        {/* Main content */}
        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar
            step={5}
            mascotSpeech="The cherry blossoms drift through the Dragon's Gate. Nirvana. The work is done. You are free."
          />

          {/* Main panel */}
          <div style={{
            flex: 1, padding: '2rem',
            background: 'rgba(8,6,4,0.25)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          }}>
            {/* Pulsing jade checkmark */}
            <div style={{
              width: 90, height: 90, borderRadius: '50%',
              border: '2px solid #5CFFCC',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 40, color: '#5CFFCC',
              background: 'rgba(93,202,165,0.06)',
              boxShadow: '0 0 24px rgba(93,202,165,0.2)',
              animation: 'jadePulse 2.5s ease infinite',
              marginBottom: 28,
            }}>
              ✓
            </div>

            {/* Title */}
            <h1 style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: 'clamp(1.4rem, 3vw, 2rem)',
              color: '#5CFFCC',
              textShadow: '0 0 20px rgba(93,202,165,0.25)',
              letterSpacing: 3,
              textAlign: 'center',
              marginBottom: 12,
            }}>
              Done. 5 Minutes. You&apos;re Free.
            </h1>

            {/* Subtitle */}
            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 15, color: '#8A8278',
              textAlign: 'center',
              letterSpacing: 1,
              lineHeight: 1.6,
              maxWidth: 420,
            }}>
              3 Official Letters generated (One Per Bureau). The bureaus have been warned.<br />
              Download or send certified mail now.
            </p>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: 14, marginTop: 28, flexWrap: 'wrap', justifyContent: 'center' }}>
              <button
                onClick={() => {
                  const flask = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'
                  window.open(`${flask}/api/letters`, '_blank')
                }}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 14, letterSpacing: 3,
                  textTransform: 'uppercase', color: '#050403',
                  background: 'linear-gradient(135deg, #5CFFCC, #33FFB8)',
                  padding: '14px 36px', borderRadius: 4, border: 'none',
                  cursor: 'pointer',
                  boxShadow: '0 4px 20px rgba(93,202,165,0.3)',
                }}
              >
                ⬇ Download All Letters
              </button>
            </div>

            {/* Mail options */}
            <div style={{
              marginTop: 20, width: '100%', maxWidth: 480,
              border: '1px solid rgba(93,202,165,0.15)',
              borderRadius: 6, padding: '1rem',
              background: 'rgba(6,4,2,0.6)',
            }}>
              <p style={{
                fontFamily: 'var(--font-cinzel), serif', fontSize: '0.72rem',
                color: '#5CFFCC', letterSpacing: 1.5, marginBottom: 12,
              }}>
                ✉ Mail Options
              </p>

              {/* Radio: Standard */}
              <label style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                borderRadius: 4, cursor: 'pointer', marginBottom: 6,
                border: mailClass === 'first' ? '1px solid rgba(93,202,165,0.4)' : '1px solid rgba(138,130,120,0.15)',
                background: mailClass === 'first' ? 'rgba(93,202,165,0.06)' : 'transparent',
                transition: 'all 0.2s',
              }}>
                <input
                  type="radio" name="mailClass" value="first"
                  checked={mailClass === 'first'}
                  onChange={() => setMailClass('first')}
                  style={{ accentColor: '#5CFFCC' }}
                />
                <div>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0' }}>
                    Standard Mail with Tracking
                  </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#5CFFCC', marginLeft: 8 }}>
                    $3/letter
                  </span>
                </div>
              </label>

              {/* Radio: Certified */}
              <label style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                borderRadius: 4, cursor: 'pointer',
                border: mailClass === 'certified' ? '1px solid rgba(93,202,165,0.4)' : '1px solid rgba(138,130,120,0.15)',
                background: mailClass === 'certified' ? 'rgba(93,202,165,0.06)' : 'transparent',
                transition: 'all 0.2s',
              }}>
                <input
                  type="radio" name="mailClass" value="certified"
                  checked={mailClass === 'certified'}
                  onChange={() => setMailClass('certified')}
                  style={{ accentColor: '#5CFFCC' }}
                />
                <div>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0' }}>
                    Certified Mail
                  </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#5CFFCC', marginLeft: 8 }}>
                    $8/letter
                  </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 10, color: '#8A8278', display: 'block', marginTop: 2 }}>
                    Recommended — proof of delivery for FCRA disputes
                  </span>
                </div>
              </label>

              {/* Send button */}
              <button
                disabled={sending}
                onClick={async () => {
                  setSending(true)
                  setMailResult('')
                  try {
                    const flask = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'
                    const res = await fetch(`${flask}/api/send-certified`, {
                      method: 'POST',
                      credentials: 'include',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ mailClass: mailClass === 'certified' ? 'Certified Mail' : 'First Class' }),
                    })
                    const data = await res.json()
                    if (data.sent > 0) {
                      setMailResult(`✓ ${data.sent} letter${data.sent > 1 ? 's' : ''} sent via ${mailClass === 'certified' ? 'Certified Mail' : 'Standard Mail'}`)
                    } else {
                      setMailResult(data.error || 'No letters sent')
                    }
                  } catch {
                    setMailResult('Failed to connect')
                  } finally {
                    setSending(false)
                  }
                }}
                style={{
                  width: '100%', marginTop: 12,
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: '#5CFFCC',
                  background: 'transparent',
                  padding: '12px 0', borderRadius: 4,
                  border: '1px solid rgba(93,202,165,0.4)',
                  cursor: sending ? 'wait' : 'pointer',
                  opacity: sending ? 0.6 : 1,
                }}
              >
                {sending ? 'Sending...' : `✉ Send All Letters — ${mailClass === 'certified' ? 'Certified' : 'Standard'}`}
              </button>

              {mailResult && (
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 12,
                  color: mailResult.startsWith('✓') ? '#5CFFCC' : '#FF4444',
                  textAlign: 'center', marginTop: 8,
                }}>
                  {mailResult}
                </p>
              )}
            </div>
            {/* Tip cards 2x2 */}
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12,
              marginTop: 28, width: '100%', maxWidth: 480,
            }}>
              {[
                { title: '30-Day Follow-Up', body: 'If no bureau response in 30 days, send your follow-up letter citing FCRA 611(a)(1) non-compliance.' },
                { title: 'Build Credit Now', body: 'Open a secured card, put one bill on it, pay monthly. 6 months to a score from zero.' },
                { title: '60-Day Check-In', body: 'Partial response? Send the escalation letter with case law citations. Courts side with consumers.' },
                { title: 'Peace of Mind', body: 'Your letters are FCRA-compliant, state-law cited, and certified-mail ready. The hard part is done.' },
              ].map((tip) => (
                <div key={tip.title} style={{
                  border: '1px solid rgba(93,202,165,0.3)',
                  background: 'rgba(6,4,2,0.7)',
                  borderRadius: 4,
                  padding: '0.75rem',
                }}>
                  <p style={{
                    fontFamily: 'var(--font-cinzel), serif',
                    fontSize: '0.72rem', color: '#5CFFCC',
                    letterSpacing: 1.5, marginBottom: 5,
                  }}>
                    {tip.title}
                  </p>
                  <p style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 11, color: '#8A8278',
                    lineHeight: 1.5,
                  }}>
                    {tip.body}
                  </p>
                </div>
              ))}
            </div>

            {/* Back button */}
            <button
              onClick={() => navigateTo('/step/4')}
              style={{
                marginTop: 24,
                fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                textTransform: 'uppercase', color: '#8A8278', background: 'transparent',
                padding: '10px 24px', borderRadius: 4,
                border: '1px solid rgba(138,130,120,0.3)', cursor: 'pointer',
              }}
            >
              &larr; Back
            </button>
          </div>
        </div>
    </SceneLayout>
  )
}
