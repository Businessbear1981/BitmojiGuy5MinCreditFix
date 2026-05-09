'use client'

import { useState, useEffect } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { getWatcherStatus, subscribeWatcher, getFollowupLetters } from '@/lib/api'

const ACCENT = '#8CB4FF'

interface Milestone {
  date: string
  days_remaining: number
  reached: boolean
  letter_sent: boolean
}

interface Tracking {
  dispatched: boolean
  subscribed: boolean
  dispatched_at?: string
  days_since_dispatch?: number
  milestones?: { day_30: Milestone; day_60: Milestone; day_90: Milestone }
  notify_method?: string
  notify_handle?: string
  notifications_sent?: Array<{ day: number; method: string; sent_at: string; delivered: boolean }>
  confirmation?: string
  letter_count?: number
}

const NOTIFY_OPTIONS = [
  { value: 'email', label: 'Email', icon: '\u2709' },
  { value: 'snapchat', label: 'Snapchat', icon: '\uD83D\uDC7B' },
  { value: 'tiktok', label: 'TikTok', icon: '\uD83C\uDFB5' },
  { value: 'instagram', label: 'Instagram', icon: '\uD83D\uDCF7' },
]

const PARTNERS = [
  {
    name: 'Chime',
    desc: 'Fee-free banking + credit builder card. No minimum balance.',
    promo: 'AECREDITFIX',
    type: 'Secured Card',
    color: '#00D54B',
  },
  {
    name: 'Cleo',
    desc: 'AI-powered budgeting + credit score tracking. Cash advances up to $250.',
    promo: 'AELABS2025',
    type: 'Credit Builder',
    color: '#5C6BC0',
  },
  {
    name: 'Amex Platinum',
    desc: 'Premium travel rewards. 80K welcome bonus. Global lounge access.',
    promo: 'AE-AMEX-PLAT',
    type: 'Unsecured',
    color: '#C0C0C0',
  },
  {
    name: 'Capital One Secured',
    desc: 'No annual fee. $200 minimum deposit. Reports to all 3 bureaus.',
    promo: 'AE-CAPSECURE',
    type: 'Secured Card',
    color: '#D03027',
  },
  {
    name: 'Capital One Quicksilver',
    desc: '1.5% unlimited cash back. No annual fee. Pre-qualify without affecting score.',
    promo: 'AE-CAPONE',
    type: 'Unsecured',
    color: '#D03027',
  },
]

export default function WatcherPage() {
  const { navigateTo } = useShojiNav()
  const [tracking, setTracking] = useState<Tracking | null>(null)
  const [loading, setLoading] = useState(true)
  const [notifyMethod, setNotifyMethod] = useState('email')
  const [notifyHandle, setNotifyHandle] = useState('')
  const [subscribing, setSubscribing] = useState(false)
  const [subError, setSubError] = useState('')
  const [actionStatus, setActionStatus] = useState<Record<number, string>>({})

  useEffect(() => {
    (async () => {
      try {
        const res = await getWatcherStatus()
        if (res.ok) {
          const data = await res.json()
          setTracking(data.tracking)
          if (data.tracking?.notify_method) setNotifyMethod(data.tracking.notify_method)
          if (data.tracking?.notify_handle) setNotifyHandle(data.tracking.notify_handle)
        }
      } catch { /* server down */ }
      setLoading(false)
    })()
  }, [])

  async function handleSubscribe() {
    if (!notifyHandle) { setSubError('Enter your handle or email'); return }
    setSubscribing(true); setSubError('')
    try {
      const res = await subscribeWatcher(notifyMethod, notifyHandle, 'manual')
      const data = await res.json()
      if (data.ok || data.subscribed || data.already) {
        setTracking((t) => t ? { ...t, subscribed: true, notify_method: notifyMethod, notify_handle: notifyHandle } : t)
      } else if (data.checkout_url) {
        window.location.href = data.checkout_url
      } else {
        setSubError(data.error || 'Subscription failed')
      }
    } catch {
      setSubError('Cannot connect to server')
    }
    setSubscribing(false)
  }

  async function handleFollowup(day: number) {
    setActionStatus((s) => ({ ...s, [day]: 'loading' }))
    try {
      const res = await getFollowupLetters(day)
      const data = await res.json()
      if (data.ok || data.letters) {
        setActionStatus((s) => ({ ...s, [day]: `${data.letters?.length || 0} letters ready` }))
      } else {
        setActionStatus((s) => ({ ...s, [day]: data.error || 'Not available yet' }))
      }
    } catch {
      setActionStatus((s) => ({ ...s, [day]: 'Server not connected' }))
    }
  }

  const milestones = tracking?.milestones
  const dispatched = tracking?.dispatched

  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/watcher.png" alt="" style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', objectFit: 'cover', zIndex: 0 }} />
      <div style={{ position: 'relative', zIndex: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopNav currentStep={7} />

        <div style={{
          padding: '8px 24px', textAlign: 'center',
          background: 'rgba(140,180,255,0.05)', borderBottom: '1px solid rgba(140,180,255,0.15)',
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: ACCENT, letterSpacing: 2,
          textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 12px ${ACCENT}88, 0 0 24px ${ACCENT}44`,
        }}>
          &ldquo;From the rooftop, you see everything. The bureaus have 30 days. You have patience.&rdquo;
        </div>

        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar step={7} mascotSpeech="The Watcher tracks every deadline. 30, 60, 90 days. Each milestone has a weapon." />

          <div style={{ flex: 1, padding: '2rem', background: 'rgba(6,8,14,0.25)', display: 'flex', flexDirection: 'column', alignItems: 'center', overflowY: 'auto' }}>
            <div style={{ width: '100%', maxWidth: 720 }}>
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>
                Step 7 of 7 &middot; 眼 &middot; The Watcher
              </p>
              <h2 style={{
                fontFamily: 'var(--font-cinzel-decorative), serif',
                fontSize: '1.6rem', color: '#F0EBE0', letterSpacing: 2,
                marginTop: 0, marginBottom: 6,
                textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 24px ${ACCENT}88, 0 0 48px ${ACCENT}44`,
              }}>
                30 / 60 / 90 Day Tracker
              </h2>

              {loading ? (
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278', padding: '2rem', textAlign: 'center' }}>Loading tracking data...</p>
              ) : !tracking?.subscribed ? (
                /* ═══ SUBSCRIPTION GATE ═══ */
                <div style={{ marginBottom: 28 }}>
                  <div style={{
                    textAlign: 'center', padding: '2rem',
                    background: `linear-gradient(135deg, ${ACCENT}15, rgba(0,0,0,0.5))`,
                    border: `1px solid ${ACCENT}33`, borderRadius: 8,
                    boxShadow: `0 0 40px ${ACCENT}15`, marginBottom: 20,
                  }}>
                    <p style={{ fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '2.2rem', color: ACCENT, textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 20px ${ACCENT}AA, 0 0 40px ${ACCENT}55`, letterSpacing: 3, margin: 0 }}>
                      $10.99
                    </p>
                    <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#A8A29A', marginTop: 10, lineHeight: 1.5 }}>
                      The Watcher tracks your dispute deadlines &middot; Sends you reminders at 30, 60, and 90 days &middot; Generates escalation letters automatically
                    </p>
                  </div>

                  {/* Notification preference */}
                  <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 11, color: ACCENT, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
                    How should we notify you?
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 16 }}>
                    {NOTIFY_OPTIONS.map((opt) => (
                      <button key={opt.value} onClick={() => setNotifyMethod(opt.value)} style={{
                        padding: '12px 8px', borderRadius: 6, cursor: 'pointer',
                        background: notifyMethod === opt.value ? `${ACCENT}22` : 'rgba(0,0,0,0.4)',
                        border: `1px solid ${notifyMethod === opt.value ? ACCENT + '66' : 'rgba(138,130,120,0.15)'}`,
                        color: notifyMethod === opt.value ? ACCENT : '#8A8278',
                        fontFamily: 'var(--font-body)', fontSize: 11, textAlign: 'center',
                        transition: 'all 0.2s',
                        textShadow: `0 0 8px currentColor, 0 0 20px currentColor${notifyMethod === opt.value ? `, 0 0 8px ${ACCENT}44` : ''}`,
                      }}>
                        <div style={{ fontSize: 18, marginBottom: 4 }}>{opt.icon}</div>
                        {opt.label}
                      </button>
                    ))}
                  </div>

                  <input
                    type="text"
                    value={notifyHandle}
                    onChange={(e) => setNotifyHandle(e.target.value)}
                    placeholder={notifyMethod === 'email' ? 'your@email.com' : `@your${notifyMethod}handle`}
                    style={{
                      width: '100%', padding: '12px 14px', marginBottom: 12,
                      background: 'rgba(10,8,4,0.85)', border: `1px solid ${ACCENT}33`,
                      borderRadius: 4, color: '#F0EBE0', fontFamily: 'var(--font-body)', fontSize: 14, outline: 'none',
                    }}
                  />

                  {subError && <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#FF6B6B', marginBottom: 12 }}>{subError}</p>}

                  <button onClick={handleSubscribe} disabled={subscribing} style={{
                    width: '100%', padding: '14px',
                    fontFamily: 'var(--font-heading)', fontSize: 15, letterSpacing: 3, textTransform: 'uppercase',
                    color: '#050403', background: `linear-gradient(135deg, ${ACCENT}, #3A5FB3)`,
                    border: 'none', borderRadius: 4, cursor: subscribing ? 'wait' : 'pointer',
                    boxShadow: `0 4px 24px ${ACCENT}55`, opacity: subscribing ? 0.7 : 1,
                  }}>
                    {subscribing ? 'Processing...' : 'Activate The Watcher \u2014 $10.99'}
                  </button>
                </div>
              ) : (
                /* ═══ ACTIVE TRACKING ═══ */
                <>
                  {/* Dispatch status */}
                  {dispatched && (
                    <div style={{
                      padding: '14px 16px', marginBottom: 16,
                      background: `${ACCENT}11`, borderLeft: `3px solid ${ACCENT}`, borderRadius: 4,
                    }}>
                      <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 11, color: ACCENT, letterSpacing: 2, textTransform: 'uppercase', margin: 0 }}>
                        Letters dispatched &middot; {tracking.days_since_dispatch} days ago
                      </p>
                      <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', margin: '4px 0 0' }}>
                        Conf: {tracking.confirmation} &middot; Notifying via {tracking.notify_method}: {tracking.notify_handle}
                      </p>
                    </div>
                  )}

                  {/* Milestone timeline */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 28 }}>
                    {([
                      { day: 30, title: 'First Response Window', body: 'Bureaus have 30 days under FCRA 611(a)(1). If no response, send non-compliance letter.', statute: 'FCRA 611(a)(1)', ms: milestones?.day_30 },
                      { day: 60, title: 'Escalation Checkpoint', body: 'Partial or boilerplate response? Send escalation with Cushman v. TransUnion, Johnson v. MBNA citations.', statute: 'FCRA 623(a)', ms: milestones?.day_60 },
                      { day: 90, title: 'Legal Action Threshold', body: 'Unresolved at 90 days = standing for CFPB complaint or small claims. Damages up to $1,000/violation.', statute: 'FCRA 616', ms: milestones?.day_90 },
                    ]).map((m) => {
                      const reached = m.ms?.reached
                      const remaining = m.ms?.days_remaining ?? m.day
                      const pct = dispatched ? Math.min(100, ((m.day - remaining) / m.day) * 100) : 0
                      return (
                        <div key={m.day} style={{
                          display: 'flex', gap: 16, alignItems: 'flex-start',
                          padding: '18px 20px',
                          background: reached ? `${ACCENT}0A` : 'rgba(0,0,0,0.35)',
                          border: `1px solid ${reached ? ACCENT + '55' : ACCENT + '22'}`,
                          borderRadius: 6,
                        }}>
                          <div style={{
                            flexShrink: 0, width: 72, height: 72, borderRadius: '50%',
                            border: `2px solid ${reached ? '#5CFFCC' : ACCENT}`,
                            background: reached ? 'rgba(92,255,204,0.1)' : `${ACCENT}11`,
                            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                            boxShadow: reached ? '0 0 14px rgba(92,255,204,0.3)' : `0 0 14px ${ACCENT}33`,
                          }}>
                            <span style={{ fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '1.4rem', color: reached ? '#5CFFCC' : ACCENT, lineHeight: 1 }}>
                              {reached ? '\u2713' : remaining}
                            </span>
                            <span style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 9, color: reached ? '#5CFFCC' : ACCENT, letterSpacing: 1.5, textTransform: 'uppercase', marginTop: 2 }}>
                              {reached ? 'Done' : 'Days'}
                            </span>
                          </div>

                          <div style={{ flex: 1 }}>
                            <p style={{ fontFamily: 'var(--font-heading)', fontSize: '0.95rem', color: '#F0EBE0', letterSpacing: 1, marginBottom: 4 }}>
                              {m.title}
                            </p>
                            {/* Progress bar */}
                            {dispatched && (
                              <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, marginBottom: 8, overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${pct}%`, background: reached ? '#5CFFCC' : ACCENT, borderRadius: 2, transition: 'width 0.5s' }} />
                              </div>
                            )}
                            <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#A8A29A', lineHeight: 1.55, marginBottom: 10 }}>{m.body}</p>
                            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                              <span style={{
                                fontFamily: 'var(--font-body)', fontSize: 10, letterSpacing: 1.5, textTransform: 'uppercase',
                                color: ACCENT, padding: '3px 10px', borderRadius: 3, border: `1px solid ${ACCENT}44`,
                              }}>
                                {m.statute}
                              </span>
                              <button onClick={() => handleFollowup(m.day)} disabled={actionStatus[m.day] === 'loading'} style={{
                                fontFamily: 'var(--font-heading)', fontSize: 11, letterSpacing: 2, textTransform: 'uppercase',
                                color: reached ? '#5CFFCC' : ACCENT, background: 'transparent',
                                padding: '6px 14px', borderRadius: 3, border: `1px solid ${reached ? 'rgba(92,255,204,0.4)' : ACCENT + '66'}`,
                                cursor: actionStatus[m.day] === 'loading' ? 'wait' : 'pointer',
                              }}>
                                {actionStatus[m.day] === 'loading' ? 'Loading...' : actionStatus[m.day] || (reached ? 'Download Letter' : `${remaining} days left`)}
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {/* Notification log */}
                  {tracking.notifications_sent && tracking.notifications_sent.length > 0 && (
                    <div style={{ marginBottom: 24, padding: '14px 16px', background: 'rgba(0,0,0,0.3)', borderRadius: 6, border: `1px solid ${ACCENT}15` }}>
                      <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 10, color: ACCENT, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>Notification History</p>
                      {tracking.notifications_sent.map((n, i) => (
                        <div key={i} style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#A8A29A', marginBottom: 4 }}>
                          Day {n.day} &middot; {n.method} &middot; {n.sent_at?.slice(0, 16)} &middot; {n.delivered ? '\u2713 Delivered' : 'Pending'}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}

              {/* ═══ PARTNER OFFERS ═══ */}
              <div style={{ marginBottom: 28 }}>
                <p style={{
                  fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '1.1rem',
                  color: '#F0EBE0', letterSpacing: 2, marginBottom: 4,
                  textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 16px ${ACCENT}55`,
                }}>
                  Rebuild Stronger
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#8A8278', fontStyle: 'italic', marginBottom: 16 }}>
                  Exclusive partner offers to build credit after your disputes clear
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {PARTNERS.map((p) => (
                    <div key={p.name} style={{
                      display: 'flex', alignItems: 'center', gap: 16, padding: '16px 18px',
                      background: 'rgba(0,0,0,0.35)', border: `1px solid ${p.color}33`,
                      borderRadius: 6, transition: 'border-color 0.2s',
                    }}>
                      <div style={{
                        flexShrink: 0, width: 48, height: 48, borderRadius: 8,
                        background: `${p.color}22`, border: `1px solid ${p.color}44`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontFamily: 'var(--font-cinzel), serif', fontSize: 11,
                        color: p.color, fontWeight: 700, letterSpacing: 1,
                        textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 8px ${p.color}44`,
                      }}>
                        {p.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 3 }}>
                          <span style={{ fontFamily: 'var(--font-heading)', fontSize: 13, color: '#F0EBE0', letterSpacing: 0.5 }}>{p.name}</span>
                          <span style={{
                            fontFamily: 'var(--font-body)', fontSize: 9, letterSpacing: 1,
                            padding: '2px 6px', borderRadius: 3,
                            color: p.color, border: `1px solid ${p.color}44`,
                            textTransform: 'uppercase',
                          }}>
                            {p.type}
                          </span>
                        </div>
                        <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#A8A29A', margin: 0, lineHeight: 1.4 }}>{p.desc}</p>
                      </div>
                      <div style={{ textAlign: 'right', flexShrink: 0 }}>
                        <p style={{ fontFamily: 'var(--font-body)', fontSize: 9, color: '#8A8278', letterSpacing: 1, textTransform: 'uppercase', margin: '0 0 4px' }}>Promo Code</p>
                        <span style={{
                          fontFamily: 'monospace', fontSize: 12, color: p.color,
                          padding: '4px 10px', borderRadius: 4,
                          background: `${p.color}15`, border: `1px solid ${p.color}33`,
                          letterSpacing: 1.5,
                          textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 6px ${p.color}44`,
                        }}>
                          {p.promo}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Nav */}
              <div style={{ display: 'flex', gap: 12, justifyContent: 'space-between' }}>
                <button onClick={() => navigateTo('/gate')} style={{
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: '#8A8278', background: 'transparent',
                  padding: '10px 24px', borderRadius: 4,
                  border: '1px solid rgba(138,130,120,0.3)', cursor: 'pointer',
                }}>
                  &larr; Back
                </button>
                <button onClick={() => navigateTo('/')} style={{
                  fontFamily: 'var(--font-heading)', fontSize: 14, letterSpacing: 3,
                  textTransform: 'uppercase', color: '#050403',
                  background: `linear-gradient(135deg, ${ACCENT}, #3A5FB3)`,
                  padding: '12px 40px', borderRadius: 4, border: 'none', cursor: 'pointer',
                  boxShadow: `0 4px 20px ${ACCENT}55`,
                }}>
                  Return to Start
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
