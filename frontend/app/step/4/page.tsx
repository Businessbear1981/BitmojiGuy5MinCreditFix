'use client'

import { useState } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { useWizardStore } from '@/store/wizardStore'
import { SceneLayout } from '@/components/scene/SceneLayout'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { createCheckout } from '@/lib/api'

export default function Step4Page() {
  const { navigateTo } = useShojiNav()
  const { setPaid } = useWizardStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handlePay() {
    setError('')
    setLoading(true)
    try {
      const res = await createCheckout()
      const data = await res.json()
      if (data.dev_mode) {
        // Dev mode — no Stripe key, skip payment
        setPaid(true)
        navigateTo('/step/5')
      } else if (data.checkout_url) {
        // Redirect to Stripe hosted checkout
        window.location.href = data.checkout_url
      } else {
        throw new Error(data.error || 'Could not create checkout session')
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Payment failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SceneLayout preset="gold">
        <TopNav currentStep={4} />

        {/* Zen strip */}
        <div style={{
          padding: '8px 24px', textAlign: 'center',
          background: 'rgba(239,159,39,0.04)', borderBottom: '1px solid rgba(239,159,39,0.1)',
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: '#EF9F27', letterSpacing: 2,
        }}>
          &ldquo;The earth does not move &mdash; it holds everything. This is gold.&rdquo;
        </div>

        {/* Main content */}
        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar
            step={4}
            mascotSpeech="The raked sand holds the shape of your intention. One payment. The earth records it."
          />

          {/* Main panel */}
          <div style={{
            flex: 1, padding: '2rem',
            background: 'rgba(14,10,4,0.25)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          }}>
            {/* Payment card */}
            <div style={{
              width: '100%', maxWidth: 440,
              background: 'rgba(10,8,4,0.7)',
              border: '1px solid rgba(239,159,39,0.15)',
              borderRadius: 8,
              padding: '2.5rem 2rem',
            }}>
              {/* Price */}
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <p style={{
                  fontFamily: 'var(--font-cinzel-decorative), serif',
                  fontSize: '2rem', color: '#EF9F27',
                  textShadow: '0 0 16px rgba(239,159,39,0.25)',
                  letterSpacing: 2, lineHeight: 1,
                }}>
                  $24.99
                </p>
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 12, color: '#8A8278',
                  letterSpacing: 1, marginTop: 8, lineHeight: 1.5,
                }}>
                  Full dispute package &middot; 15 letters &middot; All bureaus &middot; Certified mail ready
                </p>
              </div>

              {/* Divider */}
              <div style={{ height: 1, background: 'rgba(239,159,39,0.1)', marginBottom: 24 }} />

              {/* Card input area — Stripe Elements placeholder */}
              <div style={{ marginBottom: 20 }}>
                <label style={{
                  fontFamily: 'var(--font-cinzel), serif', fontSize: '0.65rem',
                  color: '#EF9F27', letterSpacing: 2, textTransform: 'uppercase',
                  display: 'block', marginBottom: 6,
                }}>
                  Card Number
                </label>
                <div style={{
                  background: 'rgba(10,8,4,0.9)',
                  border: '1px solid rgba(239,159,39,0.2)',
                  borderRadius: 4, padding: '12px 14px',
                  fontFamily: 'var(--font-body)', fontSize: 14, color: '#8A8278',
                  letterSpacing: 2,
                }}>
                  4242 &middot;&middot;&middot;&middot; &middot;&middot;&middot;&middot; &middot;&middot;&middot;&middot;
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 24 }}>
                <div>
                  <label style={{
                    fontFamily: 'var(--font-cinzel), serif', fontSize: '0.65rem',
                    color: '#EF9F27', letterSpacing: 2, textTransform: 'uppercase',
                    display: 'block', marginBottom: 6,
                  }}>
                    Expiry
                  </label>
                  <div style={{
                    background: 'rgba(10,8,4,0.9)',
                    border: '1px solid rgba(239,159,39,0.2)',
                    borderRadius: 4, padding: '12px 14px',
                    fontFamily: 'var(--font-body)', fontSize: 14, color: '#8A8278',
                    letterSpacing: 2,
                  }}>
                    MM / YY
                  </div>
                </div>
                <div>
                  <label style={{
                    fontFamily: 'var(--font-cinzel), serif', fontSize: '0.65rem',
                    color: '#EF9F27', letterSpacing: 2, textTransform: 'uppercase',
                    display: 'block', marginBottom: 6,
                  }}>
                    CVV
                  </label>
                  <div style={{
                    background: 'rgba(10,8,4,0.9)',
                    border: '1px solid rgba(239,159,39,0.2)',
                    borderRadius: 4, padding: '12px 14px',
                    fontFamily: 'var(--font-body)', fontSize: 14, color: '#8A8278',
                    letterSpacing: 2,
                  }}>
                    &middot;&middot;&middot;
                  </div>
                </div>
              </div>

              {/* Security note */}
              <p style={{
                textAlign: 'center', fontFamily: 'var(--font-body)',
                fontSize: 11, color: '#8A8278', opacity: 0.6,
                letterSpacing: 1, marginBottom: 20,
              }}>
                &#128274; Secured by Stripe &middot; PCI DSS Compliant
              </p>

              {/* Error */}
              {error && (
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 13,
                  color: '#FF4444', textAlign: 'center', marginBottom: 12,
                }}>
                  {error}
                </p>
              )}

              {/* Pay button */}
              <button
                onClick={handlePay}
                disabled={loading}
                style={{
                  width: '100%',
                  fontFamily: 'var(--font-heading)', fontSize: 15, letterSpacing: 3,
                  textTransform: 'uppercase', color: '#050403',
                  background: 'linear-gradient(135deg, #EF9F27, #A06810)',
                  padding: '14px 0', borderRadius: 4, border: 'none',
                  cursor: loading ? 'wait' : 'pointer',
                  boxShadow: '0 4px 24px rgba(239,159,39,0.3)',
                  opacity: loading ? 0.7 : 1,
                  transition: 'all 0.2s',
                }}
              >
                {loading ? 'Connecting to Stripe...' : 'Pay $24.99 — Enter the Gate →'}
              </button>
            </div>

            {/* Back button below card */}
            <button
              onClick={() => navigateTo('/step/3')}
              style={{
                marginTop: 20,
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
    </SceneLayout>
  )
}
