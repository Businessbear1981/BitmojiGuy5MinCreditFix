'use client'

import { useState, useEffect } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { getDisputes, reviewDisputes, getDisclosures } from '@/lib/api'
import type { DisclosureAck } from '@/lib/api'

const ACCENT = '#33FFB8'

interface DisputeItem {
  // Identifies which parsed suggestion this row is. Must survive the round
  // trip to reviewDisputes(), or every authorised row collapses onto the
  // first suggestion in the list.
  suggestion_index: number
  creditor: string
  account_number: string
  type: string
  amount: string
  date: string
  dispute: boolean
  dispute_box: string
  dispute_label: string
  sol_expired?: boolean
  account_age_years?: number
  // fallback fields from regex parser
  text?: string
  label?: string
}

const BOX_COLORS: Record<string, string> = {
  collections: '#FF6B6B',
  late_payments: '#EF9F27',
  wrong_addresses: '#8CB4FF',
  unknown_accounts: '#C9A84C',
  aged_debt: '#D94A3B',
  inquiries: '#7F77DD',
  identity_theft: '#FF4444',
  mov_demand: '#5CFFCC',
}

export default function KoiPondPage() {
  const { navigateTo } = useShojiNav()
  const [items, setItems] = useState<DisputeItem[]>([])
  const [loading, setLoading] = useState(true)
  const [fetchedReal, setFetchedReal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  // Required acknowledgements. The backend refuses to generate letters until
  // each is affirmed, and they are the consumer's own statements — nothing
  // here may default them to true.
  const [acks, setAcks] = useState<DisclosureAck[]>([])
  const [checked, setChecked] = useState<Record<string, boolean>>({})

  useEffect(() => {
    (async () => {
      try {
        const res = await getDisputes()
        if (res.ok) {
          const data = await res.json()
          const disputeItems = data.dispute_items || []
          if (disputeItems.length > 0) {
            // Mark all as authorized by default (all negatives = disputed)
            setItems(disputeItems.map((d: DisputeItem) => ({ ...d, dispute: true })))
            setFetchedReal(true)
          }
        }
        const disclosures = await getDisclosures()
        if (disclosures) setAcks(disclosures.acknowledgements || [])
      } catch {
        // Backend unreachable — surfaced by the error state below.
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const allAcked = acks.length > 0 && acks.every((a) => checked[a.id])

  function toggle(index: number) {
    setItems((prev) => prev.map((d, i) => i === index ? { ...d, dispute: !d.dispute } : d))
  }

  const authorizedCount = items.filter((d) => d.dispute).length

  async function handleContinue() {
    if (authorizedCount === 0) return
    if (!allAcked) {
      setError('Please read and confirm each statement below before generating your letters.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const authorized = items.filter((d) => d.dispute).map((d) => ({
        // Carries the row's identity through to the backend. Without it every
        // authorised row collapsed onto the first parsed suggestion.
        suggestion_index: d.suggestion_index,
        type: d.dispute_box || d.type || 'unknown_accounts',
        text: d.creditor
          ? `${d.creditor} ${d.account_number} ${d.amount} ${d.date}`.trim()
          : (d.text || d.label || 'Disputed item'),
        creditor: d.creditor || '',
        account_number: d.account_number || '',
        amount: d.amount || '',
      }))
      const res = await reviewDisputes(authorized, [], checked)
      const data = await res.json()
      if (data.ok) {
        navigateTo('/garden')
      } else {
        setError(data.error || 'Review failed')
      }
    } catch {
      setError('Could not connect to server.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', position: 'relative', overflow: 'hidden', background: '#050306' }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/koipond-meshy.png"
        alt=""
        style={{
          position: 'fixed', top: 0, left: 0,
          width: '100vw', height: '100vh',
          objectFit: 'cover', zIndex: 0,
        }}
      />

      <div style={{
        position: 'absolute', inset: 0, zIndex: 4, pointerEvents: 'none',
        background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.6) 100%)',
      }} />

      <div style={{ position: 'relative', zIndex: 10, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopNav currentStep={3} />

        <div style={{
          padding: '8px 24px', textAlign: 'center',
          background: `${ACCENT}0A`, borderBottom: `1px solid ${ACCENT}22`,
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: ACCENT, letterSpacing: 2,
          textShadow: `0 0 12px ${ACCENT}88, 0 0 24px ${ACCENT}44`,
        }}>
          &ldquo;The koi swims upstream. You decide which currents to fight.&rdquo;
        </div>

        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar
            step={3}
            mascotSpeech="Every negative item is flagged. Deselect any you don't want to dispute."
          />

          <div style={{
            flex: 1, padding: '2rem',
            background: 'rgba(4,10,8,0.2)',
          }}>
            <div style={{ maxWidth: 760, margin: '0 auto' }}>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT,
                letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4,
              }}>
                Step 3 of 7 &middot; 水 &middot; The Koi Pond
              </p>
              <h2 style={{
                fontFamily: 'var(--font-cinzel-decorative), serif',
                fontSize: '1.6rem', color: '#F0EBE0', letterSpacing: 2,
                marginTop: 0, marginBottom: 6,
                textShadow: `0 0 24px ${ACCENT}88, 0 0 48px ${ACCENT}44`,
              }}>
                Authorize Your Disputes
              </h2>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278',
                fontStyle: 'italic', marginBottom: 20,
              }}>
                {fetchedReal
                  ? `${items.length} negative items found in your report. All are pre-selected for dispute.`
                  : 'Upload your credit report in the Dojo to populate disputes.'}
              </p>

              {/* Summary strip */}
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '12px 16px',
                background: `${ACCENT}11`, borderLeft: `3px solid ${ACCENT}`,
                borderRadius: 4, marginBottom: 16,
              }}>
                <span style={{
                  fontFamily: 'var(--font-cinzel), serif', fontSize: 13,
                  color: ACCENT, letterSpacing: 2, textTransform: 'uppercase',
                }}>
                  {authorizedCount} of {items.length} authorized
                </span>
                <span style={{
                  fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
                }}>
                  Tap any row to toggle
                </span>
              </div>

              {loading ? (
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278', textAlign: 'center', padding: '2rem' }}>
                  Loading disputes...
                </p>
              ) : items.length === 0 ? (
                <div style={{
                  textAlign: 'center', padding: '3rem',
                  background: 'rgba(0,0,0,0.3)', borderRadius: 6,
                  border: `1px solid ${ACCENT}22`, marginBottom: 24,
                }}>
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: '#8A8278' }}>
                    No disputes found. Go back to the Dojo and upload your credit report.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24 }}>
                  {items.map((d, i) => (
                    <button
                      key={i}
                      onClick={() => toggle(i)}
                      style={{
                        textAlign: 'left', cursor: 'pointer',
                        display: 'grid', gridTemplateColumns: '36px 1fr auto',
                        alignItems: 'center', gap: 14,
                        padding: '14px 16px',
                        background: d.dispute ? `${ACCENT}0F` : 'rgba(0,0,0,0.4)',
                        border: `1px solid ${d.dispute ? ACCENT + '66' : 'rgba(138,130,120,0.15)'}`,
                        borderRadius: 6,
                        transition: 'all 0.2s',
                      }}
                    >
                      {/* Checkbox */}
                      <div style={{
                        width: 28, height: 28, borderRadius: 4,
                        border: `2px solid ${d.dispute ? ACCENT : '#5A5A5A'}`,
                        background: d.dispute ? ACCENT : 'transparent',
                        color: '#050403',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 14, fontWeight: 700,
                        boxShadow: d.dispute ? `0 0 10px ${ACCENT}66` : 'none',
                      }}>
                        {d.dispute ? '\u2713' : ''}
                      </div>

                      {/* Details */}
                      <div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 3 }}>
                          <span style={{
                            fontFamily: 'var(--font-body)', fontSize: 9, letterSpacing: 1.5,
                            textTransform: 'uppercase',
                            color: BOX_COLORS[d.dispute_box] || ACCENT,
                            padding: '2px 6px', borderRadius: 3,
                            border: `1px solid ${(BOX_COLORS[d.dispute_box] || ACCENT) + '44'}`,
                          }}>
                            {d.dispute_label || d.type || 'Dispute'}
                          </span>
                          {d.sol_expired && (
                            <span style={{
                              fontFamily: 'var(--font-body)', fontSize: 9,
                              color: '#D94A3B', letterSpacing: 1,
                              padding: '2px 6px', borderRadius: 3,
                              border: '1px solid rgba(217,74,59,0.4)',
                            }}>
                              SOL EXPIRED
                            </span>
                          )}
                        </div>
                        <p style={{ fontFamily: 'var(--font-heading)', fontSize: 13, color: '#F0EBE0', margin: 0, letterSpacing: 0.5 }}>
                          {d.creditor || d.text || 'Disputed Item'}
                        </p>
                        <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', margin: 0 }}>
                          {[d.account_number && `Acct: ${d.account_number}`, d.amount, d.date].filter(Boolean).join(' \u00B7 ') || d.label || ''}
                        </p>
                      </div>

                      {/* Age indicator */}
                      <div style={{ textAlign: 'right' }}>
                        {d.account_age_years && (
                          <span style={{
                            fontFamily: 'var(--font-body)', fontSize: 10, letterSpacing: 1,
                            color: '#8A8278', whiteSpace: 'nowrap',
                          }}>
                            {d.account_age_years}yr old
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {acks.length > 0 && (
                <div style={{
                  marginBottom: 24, padding: '16px 18px',
                  background: 'rgba(0,0,0,0.45)', borderRadius: 6,
                  border: `1px solid ${allAcked ? ACCENT + '55' : 'rgba(201,168,76,0.45)'}`,
                }}>
                  <p style={{
                    fontFamily: 'var(--font-cinzel), serif', fontSize: 12,
                    letterSpacing: 2, textTransform: 'uppercase',
                    color: allAcked ? ACCENT : '#C9A84C', margin: '0 0 4px',
                  }}>
                    Before your letters are written
                  </p>
                  <p style={{
                    fontFamily: 'var(--font-body)', fontSize: 12, color: '#8A8278',
                    fontStyle: 'italic', margin: '0 0 14px',
                  }}>
                    These are your letters, signed in your name. Please confirm each
                    statement — all {acks.length} are required.
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {acks.map((a) => (
                      <label key={a.id} style={{
                        display: 'grid', gridTemplateColumns: '22px 1fr', gap: 12,
                        alignItems: 'start', cursor: 'pointer',
                      }}>
                        <input
                          type="checkbox"
                          checked={!!checked[a.id]}
                          onChange={(e) =>
                            setChecked((prev) => ({ ...prev, [a.id]: e.target.checked }))}
                          style={{ width: 18, height: 18, marginTop: 2, accentColor: ACCENT, cursor: 'pointer' }}
                        />
                        <span style={{
                          fontFamily: 'var(--font-body)', fontSize: 12.5,
                          color: checked[a.id] ? '#F0EBE0' : '#A9A29A', lineHeight: 1.5,
                        }}>
                          {a.label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {error && (
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 13, color: '#FF4444',
                  textAlign: 'center', marginBottom: 12,
                }}>
                  {error}
                </p>
              )}

              <div style={{ display: 'flex', gap: 12, justifyContent: 'space-between' }}>
                <button
                  onClick={() => navigateTo('/dojo')}
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
                  onClick={handleContinue}
                  disabled={authorizedCount === 0 || !allAcked || submitting}
                  style={{
                    fontFamily: 'var(--font-heading)', fontSize: 14, letterSpacing: 3,
                    textTransform: 'uppercase', color: '#050403',
                    background: (authorizedCount === 0 || !allAcked)
                      ? 'rgba(100,100,100,0.3)'
                      : `linear-gradient(135deg, ${ACCENT}, #1ADB8E)`,
                    padding: '12px 40px', borderRadius: 4, border: 'none',
                    cursor: (authorizedCount === 0 || !allAcked || submitting) ? 'not-allowed' : 'pointer',
                    boxShadow: (authorizedCount > 0 && allAcked) ? `0 4px 20px ${ACCENT}55` : 'none',
                    opacity: (authorizedCount === 0 || !allAcked) ? 0.5 : 1,
                  }}
                >
                  {submitting
                    ? 'Generating Letters...'
                    : `Generate ${authorizedCount > 0 ? '' : ''}Letters \u2192`}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
