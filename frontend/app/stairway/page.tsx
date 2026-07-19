'use client'

import { useState, useEffect } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { useWizardStore } from '@/store/wizardStore'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { createCheckout, getCaseStatus, manualPay, queueForRelease, setApiSessionId } from '@/lib/api'
import { MANUAL_PAY_HANDLES, type ManualPayPending } from '@/lib/types'

const ACCENT = '#5CFFCC'

export default function StairwayPage() {
  const { navigateTo } = useShojiNav()
  const { setPaid } = useWizardStore()
  const [loading, setLoading] = useState<'card' | 'cashapp' | 'chime' | null>(null)
  const [error, setError] = useState('')
  const [pending, setPending] = useState<ManualPayPending | null>(null)

  // Stripe cancel_url lands back here with ?session_id= — restore the session
  // so the customer can retry payment after a refresh. Also restore a manual
  // (Cash App / Chime) payment that's still awaiting verification.
  useEffect(() => {
    const sid = new URLSearchParams(window.location.search).get('session_id')
    if (sid) setApiSessionId(sid)
    ;(async () => {
      try {
        const status = await getCaseStatus()
        if (status?.paid) {
          setPaid(true)
          navigateTo('/gate')
        } else if (status?.manual_pay_pending && status.manual_pay_code) {
          const method = status.manual_pay_method === 'chime' ? 'chime' : 'cashapp'
          setPending({
            confirmation: status.manual_pay_code,
            method,
            handle: MANUAL_PAY_HANDLES[method].handle,
            amount: '$24.99',
          })
        }
      } catch { /* no session yet */ }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // While a manual payment is pending, poll for the admin release and walk
  // the customer through the gate the moment their letters unlock.
  useEffect(() => {
    if (!pending) return
    const timer = setInterval(async () => {
      try {
        const status = await getCaseStatus()
        if (status?.paid) {
          clearInterval(timer)
          setPaid(true)
          navigateTo('/gate')
        }
      } catch { /* server unreachable — keep polling */ }
    }, 5000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pending])

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

  async function handleManual(method: 'cashapp' | 'chime') {
    setError(''); setLoading(method)
    try {
      const res = await manualPay(method)
      const data = await res.json()
      if (data.pending) {
        setPending({
          confirmation: data.confirmation || '',
          method,
          handle: data.handle || MANUAL_PAY_HANDLES[method].handle,
          amount: data.amount || '$24.99',
        })
      } else if (data.ok && data.paid) {
        setPaid(true)
        await queueForRelease()
        navigateTo('/gate')
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
                Full dispute package &middot; 3 letters &middot; All three bureaus &middot; $24.99 + postage
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

            {/* Cash App & Chime — RECOMMENDED */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
              <button
                onClick={() => handleManual('cashapp')}
                disabled={loading !== null}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: '#050403',
                  background: `linear-gradient(135deg, #00D54B, #33FFB8)`,
                  padding: '14px 16px', borderRadius: 4, border: 'none',
                  cursor: loading ? 'wait' : 'pointer',
                  opacity: loading === 'cashapp' ? 0.7 : 1,
                  position: 'relative',
                }}
              >
                <span style={{ position: 'absolute', top: -8, right: 8, fontSize: 9, background: '#00D54B', color: '#050403', padding: '2px 6px', borderRadius: 3, letterSpacing: 1 }}>RECOMMENDED</span>
                {loading === 'cashapp' ? 'Processing...' : `Cash App · ${MANUAL_PAY_HANDLES.cashapp.handle}`}
              </button>
              <button
                onClick={() => handleManual('chime')}
                disabled={loading !== null}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: '#050403',
                  background: `linear-gradient(135deg, #00D54B, #33FFB8)`,
                  padding: '14px 16px', borderRadius: 4, border: 'none',
                  cursor: loading ? 'wait' : 'pointer',
                  opacity: loading === 'chime' ? 0.7 : 1,
                  position: 'relative',
                }}
              >
                <span style={{ position: 'absolute', top: -8, right: 8, fontSize: 9, background: '#00D54B', color: '#050403', padding: '2px 6px', borderRadius: 3, letterSpacing: 1 }}>RECOMMENDED</span>
                {loading === 'chime' ? 'Processing...' : `Chime · ${MANUAL_PAY_HANDLES.chime.handle}`}
              </button>
            </div>

            {/* Divider */}
            <p style={{
              textAlign: 'center', color: '#8A8278', fontSize: 11, letterSpacing: 2,
              textTransform: 'uppercase', margin: '14px 0',
            }}>
              &mdash; or pay with card &mdash;
            </p>

            {/* Card pay */}
            <button
              onClick={handleCard}
              disabled={loading !== null}
              style={{
                width: '100%',
                fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                textTransform: 'uppercase', color: ACCENT,
                background: 'rgba(0,0,0,0.4)',
                padding: '12px 0', borderRadius: 4,
                border: `1px solid ${ACCENT}55`,
                cursor: loading ? 'wait' : 'pointer',
                opacity: loading === 'card' ? 0.7 : 1,
              }}
            >
              {loading === 'card' ? 'Connecting to Stripe...' : 'Pay with Card (Stripe)'}
            </button>

            {pending && (
              <div style={{
                marginTop: 16, padding: '1.25rem',
                background: `linear-gradient(135deg, ${ACCENT}15, rgba(0,0,0,0.5))`,
                border: `1px solid ${ACCENT}44`, borderRadius: 6,
                textAlign: 'center',
              }}>
                <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 11, color: ACCENT, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
                  Payment Pending Verification
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0', lineHeight: 1.6, marginBottom: 10 }}>
                  Send <strong style={{ color: ACCENT }}>{pending.amount}</strong> on{' '}
                  {MANUAL_PAY_HANDLES[pending.method].label} to{' '}
                  <strong style={{ color: ACCENT, fontFamily: 'monospace', letterSpacing: 1 }}>{pending.handle}</strong>
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#A8A29A', marginBottom: 4 }}>
                  Put this code in the payment note:
                </p>
                <p style={{ fontFamily: 'monospace', fontSize: 18, color: '#F0EBE0', letterSpacing: 3, marginTop: 0, marginBottom: 10 }}>
                  {pending.confirmation}
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#A8A29A', lineHeight: 1.5, margin: 0 }}>
                  We verify payments by hand and unlock your letters as soon as yours lands — this page will
                  move you forward automatically. Keep it open or come back any time.
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
