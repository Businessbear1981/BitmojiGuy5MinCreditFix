'use client'

import { useState } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { useWizardStore } from '@/store/wizardStore'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { createCheckout, manualPay, queueForRelease } from '@/lib/api'

const ACCENT = '#5CFFCC'

export default function StairwayPage() {
  const { navigateTo } = useShojiNav()
  const { setPaid } = useWizardStore()
  const [loading, setLoading] = useState<'card' | 'cashapp' | 'chime' | null>(null)
  const [error, setError] = useState('')

  async function handleCard() {
    setError(''); setLoading('card')
    try {
      const res = await createCheckout()
      const data = await res.json()
      if (data.dev_mode) {
        setPaid(true)
        // Queue for admin release
        await queueForRelease()
        navigateTo('/gate')
      } else if (data.checkout_url) {
        window.location.href = data.checkout_url
      } else {
        throw new Error(data.error || 'Could not create checkout session')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Payment failed')
    } finally {
      setLoading(null)
    }
  }

  const [pendingConf, setPendingConf] = useState('')

  async function handleManual(method: 'cashapp' | 'chime') {
    setError(''); setLoading(method)
    try {
      const res = await manualPay(method)
      const data = await res.json()
      if (data.ok && !data.pending) {
        setPaid(true)
        // Queue for admin release
        await queueForRelease()
        navigateTo('/gate')
      } else if (data.pending) {
        setPendingConf(data.confirmation || '')
      } else {
        throw new Error(data.error || 'Payment not recorded')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Payment failed')
    } finally {
      setLoading(null)
    }
  }

  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="https://d2xsxph8kpxj0f.cloudfront.net/310519663623353486/TFHGKZ8eZeQPrrYUXjWpCv/stairway_to_heaven_temple-YFPGZiVmoxRsi99bAXXNaA.webp"
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
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 1 }} />
      <div style={{ position: 'relative', zIndex: 2, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopNav currentStep={5} />

      <div style={{
        padding: '8px 24px', textAlign: 'center',
        background: `${ACCENT}0A`, borderBottom: `1px solid ${ACCENT}22`,
        fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
        color: ACCENT, letterSpacing: 2,
        textShadow: `0 0 12px ${ACCENT}88, 0 0 24px ${ACCENT}44`,
      }}>
        &ldquo;At the top of the staircase, there is only one gate. One toll. One payment.&rdquo;
      </div>

      <div style={{ flex: 1, display: 'flex' }}>
        <WizardSidebar
          step={5}
          mascotSpeech="Pay the toll. The staircase leads to the Dragon's Gate."
        />

        <div style={{
          flex: 1, padding: '2rem',
          background: 'rgba(8,6,4,0.25)',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
        }}>
          <div style={{ width: '100%', maxWidth: 560 }}>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT,
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4, textAlign: 'center',
            }}>
              Step 5 of 7 &middot; 階 &middot; The Stairway
            </p>
            <h2 style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: '1.8rem', color: '#F0EBE0', letterSpacing: 2,
              marginTop: 0, marginBottom: 6, textAlign: 'center',
              textShadow: `0 0 24px ${ACCENT}66`,
            }}>
              Pay the Toll
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278',
              fontStyle: 'italic', marginBottom: 28, textAlign: 'center',
            }}>
              One payment unlocks the Dragon&apos;s Gate &middot; 3 Official Letters (One Per Bureau)
            </p>

            {/* Price banner */}
            <div style={{
              textAlign: 'center',
              background: `linear-gradient(135deg, ${ACCENT}22, rgba(0,0,0,0.6))`,
              border: `1px solid ${ACCENT}44`,
              borderRadius: 8,
              padding: '1.75rem 1rem',
              marginBottom: 20,
              boxShadow: `0 0 40px ${ACCENT}22`,
            }}>
              <p style={{
                fontFamily: 'var(--font-cinzel-decorative), serif',
                fontSize: '2.6rem', color: ACCENT,
                textShadow: `0 0 20px ${ACCENT}AA, 0 0 40px ${ACCENT}66, 0 0 60px ${ACCENT}33`,
                letterSpacing: 3, lineHeight: 1,
                margin: 0,
              }}>
                $24.99
              </p>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 12, color: '#8A8278',
                letterSpacing: 1, marginTop: 10, lineHeight: 1.5,
              }}>
                Full dispute package &middot; 3 letters &middot; All three bureaus &middot; Certified mail ready
              </p>
            </div>

            {error && (
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 13, color: '#FF4444',
                textAlign: 'center', marginBottom: 12,
              }}>
                {error}
              </p>
            )}

            {/* Card pay */}
            <button
              onClick={handleCard}
              disabled={loading !== null}
              style={{
                width: '100%',
                fontFamily: 'var(--font-heading)', fontSize: 15, letterSpacing: 3,
                textTransform: 'uppercase', color: '#050403',
                background: `linear-gradient(135deg, ${ACCENT}, #33FFB8)`,
                padding: '14px 0', borderRadius: 4, border: 'none',
                cursor: loading ? 'wait' : 'pointer',
                boxShadow: `0 4px 24px ${ACCENT}55`,
                opacity: loading === 'card' ? 0.7 : 1,
                marginBottom: 12,
              }}
            >
              {loading === 'card' ? 'Connecting to Stripe...' : '💳 Pay with Card — Stripe Secure'}
            </button>

            {/* Divider */}
            <p style={{
              textAlign: 'center', color: '#8A8278', fontSize: 11, letterSpacing: 2,
              textTransform: 'uppercase', margin: '14px 0',
            }}>
              &mdash; or manual pay &mdash;
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <button
                onClick={() => handleManual('cashapp')}
                disabled={loading !== null}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: ACCENT,
                  background: 'rgba(0,0,0,0.4)',
                  padding: '12px 16px', borderRadius: 4,
                  border: `1px solid ${ACCENT}55`,
                  cursor: loading ? 'wait' : 'pointer',
                  opacity: loading === 'cashapp' ? 0.7 : 1,
                }}
              >
                Cash App · $AELabsCreditFix
              </button>
              <button
                onClick={() => handleManual('chime')}
                disabled={loading !== null}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: ACCENT,
                  background: 'rgba(0,0,0,0.4)',
                  padding: '12px 16px', borderRadius: 4,
                  border: `1px solid ${ACCENT}55`,
                  cursor: loading ? 'wait' : 'pointer',
                  opacity: loading === 'chime' ? 0.7 : 1,
                }}
              >
                Chime · $AELabsPay
              </button>
            </div>

            {pendingConf && (
              <div style={{
                marginTop: 16, padding: '1.25rem',
                background: `linear-gradient(135deg, ${ACCENT}15, rgba(0,0,0,0.5))`,
                border: `1px solid ${ACCENT}44`, borderRadius: 6,
                textAlign: 'center',
              }}>
                <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 11, color: ACCENT, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 6 }}>
                  Payment Pending Verification
                </p>
                <p style={{ fontFamily: 'monospace', fontSize: 16, color: '#F0EBE0', letterSpacing: 2, marginBottom: 8 }}>
                  {pendingConf}
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#A8A29A', lineHeight: 1.5, margin: 0 }}>
                  Send $24.99 to the address above. Include this confirmation number in the memo. Admin will verify and unlock your letters within 24 hours.
                </p>
              </div>
            )}

            <p style={{
              textAlign: 'center', fontSize: 11, color: '#8A8278', opacity: 0.6,
              letterSpacing: 1, marginTop: 20,
            }}>
              PCI DSS compliant &middot; No card data stored on our servers
            </p>

            <button
              onClick={() => navigateTo('/garden')}
              style={{
                marginTop: 20, width: '100%',
                fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                textTransform: 'uppercase', color: '#8A8278', background: 'transparent',
                padding: '10px 24px', borderRadius: 4,
                border: '1px solid rgba(138,130,120,0.3)', cursor: 'pointer',
              }}
            >
              &larr; Back to Letters
            </button>
          </div>
        </div>
      </div>
    </div>
    </>
  )
}
