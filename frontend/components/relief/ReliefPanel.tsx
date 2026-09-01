'use client'

import { useEffect, useState } from 'react'

const ACCENT = '#33FFB8'
const GOLD = '#C9A84C'
const WARN = '#EF9F27'

/**
 * Relief pathways — the routes that are not a dispute letter.
 *
 * Renders nothing at all unless the backend says a route exists, so a file
 * with no student loans and no medical accounts sees no change to the review
 * screen. When it does render, it is a collapsed card; the directory only
 * loads when someone opens it.
 *
 * Two rules this component enforces on the UI side, matching the backend:
 *   - no route is ever presented as an eligibility finding
 *   - the "no such thing as a debt-relief grant" warning is pinned at the
 *     top of the open panel, not buried at the bottom
 */

interface Route {
  program_key?: string
  route_key?: string
  program?: string
  name?: string
  kind?: string
  observed_in_report?: string
  prompted_by?: string
  worth_checking_because?: string
  generally_for?: string
  why_it_matters?: string
  what_to_do?: string
  documents_to_gather?: string[]
  verify_at?: string
  cost?: string
  note?: string
}

interface MedicalItem {
  id: string
  furnisher: string
  amount: number | null
  why_we_think_medical: string
}

interface Section {
  key: string
  title: string
  subtitle: string
  lead: string
  routes: Route[]
  items?: MedicalItem[]
  sequence_note?: string
  disclaimer: string
  free_warning?: string
  verify_at?: string
}

interface GrantReality {
  headline: string
  detail: string
  what_is_real: string
  official_directories: { name: string; url: string }[]
}

interface ReliefPayload {
  available: boolean
  sections: Section[]
  grant_reality: GrantReality
  headline: string
}

interface Summary {
  available: boolean
  label: string
  sublabel: string
  route_count: number
}

const KIND_LABEL: Record<string, string> = {
  first_step: 'Do this first',
  reduce_or_erase: 'Can erase the balance',
  may_not_be_owed: 'You may not owe this',
  consolidation: 'Consolidation',
  going_forward: 'Going forward',
}

export function ReliefPanel({ sessionId, apiBase }: { sessionId: string; apiBase: string }) {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [payload, setPayload] = useState<ReliefPayload | null>(null)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [openRoute, setOpenRoute] = useState<string>('')

  // Cheap check on mount — decides whether the card exists at all.
  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    fetch(`${apiBase}/api/case/${sessionId}/relief/summary`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (!cancelled && d?.available) setSummary(d) })
      .catch(() => { /* the review screen must not break over this */ })
    return () => { cancelled = true }
  }, [sessionId, apiBase])

  async function toggle() {
    if (open) { setOpen(false); return }
    setOpen(true)
    if (payload) return
    setLoading(true)
    try {
      const r = await fetch(`${apiBase}/api/case/${sessionId}/relief`)
      if (r.ok) setPayload(await r.json())
    } catch { /* leave the panel empty rather than erroring the page */ }
    finally { setLoading(false) }
  }

  if (!summary?.available) return null

  return (
    <div style={{
      marginBottom: 18,
      border: `1px solid ${GOLD}44`,
      borderRadius: 6,
      background: 'linear-gradient(135deg, rgba(201,168,76,0.10), rgba(0,0,0,0.42))',
      overflow: 'hidden',
    }}>
      {/* ── The trigger ─────────────────────────────────────────────── */}
      <button
        onClick={toggle}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: 14,
          padding: '14px 16px', background: 'transparent', border: 'none',
          cursor: 'pointer', textAlign: 'left',
        }}
      >
        <span style={{ fontSize: 22, flexShrink: 0 }} aria-hidden>⛩</span>
        <span style={{ flex: 1 }}>
          <span style={{
            display: 'block',
            fontFamily: 'var(--font-cinzel), serif', fontSize: 13,
            color: GOLD, letterSpacing: 1.5, textTransform: 'uppercase',
            marginBottom: 3,
          }}>
            {summary.label}
          </span>
          <span style={{
            display: 'block',
            fontFamily: 'var(--font-body)', fontSize: 11.5, color: '#B0A99C',
          }}>
            {summary.sublabel} · {summary.route_count} routes · free to apply
          </span>
        </span>
        <span style={{
          fontFamily: 'var(--font-body)', fontSize: 11, color: GOLD,
          border: `1px solid ${GOLD}55`, borderRadius: 3, padding: '4px 9px',
          flexShrink: 0, whiteSpace: 'nowrap',
        }}>
          {open ? 'Close' : 'Look'}
        </span>
      </button>

      {!open ? null : (
        <div style={{ padding: '0 16px 16px', borderTop: `1px solid ${GOLD}22` }}>
          {loading && (
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#B0A99C', padding: '14px 0' }}>
              Checking what applies to your file…
            </p>
          )}

          {payload && (
            <>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 12.5, color: '#F0EBE0',
                lineHeight: 1.65, margin: '14px 0 4px',
              }}>
                {payload.headline}
              </p>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 11.5, color: '#8F887E',
                lineHeight: 1.6, margin: '0 0 14px',
              }}>
                None of this replaces your disputes — the letters still go out. These
                are separate roads to the same place, and you can walk both.
              </p>

              {/* ── Pinned: the grant warning ────────────────────────── */}
              <div style={{
                padding: '11px 13px', marginBottom: 16,
                border: `1px solid ${WARN}55`, borderRadius: 4,
                background: 'rgba(239,159,39,0.08)',
              }}>
                <p style={{
                  fontFamily: 'var(--font-cinzel), serif', fontSize: 11,
                  letterSpacing: 1.4, textTransform: 'uppercase', color: WARN,
                  margin: '0 0 6px',
                }}>
                  ⚠ {payload.grant_reality.headline}
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11.5, color: '#D8D2C6', lineHeight: 1.6, margin: '0 0 6px' }}>
                  {payload.grant_reality.detail}
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11.5, color: '#D8D2C6', lineHeight: 1.6, margin: '0 0 8px' }}>
                  {payload.grant_reality.what_is_real}
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {payload.grant_reality.official_directories.map((d) => (
                    <a key={d.url} href={d.url} target="_blank" rel="noopener noreferrer"
                       style={{
                         fontFamily: 'var(--font-body)', fontSize: 10.5, color: WARN,
                         textDecoration: 'underline', textUnderlineOffset: 2,
                       }}>
                      {d.url.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]}
                    </a>
                  ))}
                </div>
              </div>

              {/* ── Sections ─────────────────────────────────────────── */}
              {payload.sections.map((s) => (
                <div key={s.key} style={{ marginBottom: 18 }}>
                  <p style={{
                    fontFamily: 'var(--font-cinzel), serif', fontSize: 12,
                    letterSpacing: 1.6, textTransform: 'uppercase', color: ACCENT,
                    margin: '0 0 2px',
                  }}>
                    {s.title}
                  </p>
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8F887E', margin: '0 0 8px' }}>
                    {s.subtitle}
                  </p>
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#D8D2C6', lineHeight: 1.65, margin: '0 0 10px' }}>
                    {s.lead}
                  </p>

                  {s.free_warning && (
                    <p style={{
                      fontFamily: 'var(--font-body)', fontSize: 11, color: ACCENT,
                      lineHeight: 1.6, margin: '0 0 10px', padding: '8px 10px',
                      background: `${ACCENT}0E`, borderLeft: `2px solid ${ACCENT}77`, borderRadius: 3,
                    }}>
                      {s.free_warning}
                    </p>
                  )}

                  {/* Which accounts we think are medical — and a way to say we're wrong. */}
                  {s.items && s.items.length > 0 && (
                    <div style={{ marginBottom: 10 }}>
                      {s.items.map((it) => (
                        <p key={it.id + it.furnisher} style={{
                          fontFamily: 'var(--font-body)', fontSize: 10.5, color: '#8F887E',
                          lineHeight: 1.55, margin: '0 0 4px',
                        }}>
                          <span style={{ color: '#D8D2C6' }}>{it.furnisher}</span>
                          {it.amount ? ` · $${it.amount.toLocaleString()}` : ''} — {it.why_we_think_medical}
                        </p>
                      ))}
                    </div>
                  )}

                  {s.sequence_note && (
                    <p style={{
                      fontFamily: 'var(--font-body)', fontSize: 11, color: '#D8D2C6',
                      lineHeight: 1.6, margin: '0 0 10px', fontStyle: 'italic',
                    }}>
                      {s.sequence_note}
                    </p>
                  )}

                  {/* ── Routes ───────────────────────────────────────── */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {s.routes.map((r, i) => {
                      const key = `${s.key}-${r.program_key || r.route_key || i}`
                      const title = r.program || r.name || 'Route'
                      const isOpen = openRoute === key
                      return (
                        <div key={key} style={{
                          border: `1px solid ${isOpen ? ACCENT + '55' : 'rgba(255,255,255,0.08)'}`,
                          borderRadius: 4, background: 'rgba(0,0,0,0.30)',
                        }}>
                          <button
                            onClick={() => setOpenRoute(isOpen ? '' : key)}
                            style={{
                              width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                              padding: '10px 12px', background: 'transparent',
                              border: 'none', cursor: 'pointer', textAlign: 'left',
                            }}
                          >
                            <span style={{ flex: 1 }}>
                              <span style={{
                                display: 'block', fontFamily: 'var(--font-body)',
                                fontSize: 12.5, color: '#F0EBE0', marginBottom: 2,
                              }}>
                                {title}
                              </span>
                              {r.kind && KIND_LABEL[r.kind] && (
                                <span style={{
                                  fontFamily: 'var(--font-body)', fontSize: 10,
                                  color: ACCENT, letterSpacing: 0.8,
                                  textTransform: 'uppercase',
                                }}>
                                  {KIND_LABEL[r.kind]}
                                </span>
                              )}
                            </span>
                            <span style={{ color: '#8F887E', fontSize: 12, flexShrink: 0 }}>
                              {isOpen ? '−' : '+'}
                            </span>
                          </button>

                          {isOpen && (
                            <div style={{ padding: '0 12px 12px' }}>
                              {(r.observed_in_report || r.prompted_by) && (
                                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8F887E', lineHeight: 1.6, margin: '0 0 8px' }}>
                                  <strong style={{ color: '#B0A99C' }}>Why you&rsquo;re seeing this: </strong>
                                  {r.observed_in_report || r.prompted_by}
                                </p>
                              )}
                              {(r.worth_checking_because || r.generally_for) && (
                                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11.5, color: '#D8D2C6', lineHeight: 1.65, margin: '0 0 8px' }}>
                                  {r.worth_checking_because || r.generally_for}
                                </p>
                              )}
                              {r.why_it_matters && (
                                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11.5, color: '#D8D2C6', lineHeight: 1.65, margin: '0 0 8px' }}>
                                  {r.why_it_matters}
                                </p>
                              )}
                              {r.what_to_do && (
                                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11.5, color: '#D8D2C6', lineHeight: 1.65, margin: '0 0 8px' }}>
                                  <strong style={{ color: ACCENT }}>What to do: </strong>{r.what_to_do}
                                </p>
                              )}

                              {r.documents_to_gather && r.documents_to_gather.length > 0 && (
                                <>
                                  <p style={{
                                    fontFamily: 'var(--font-cinzel), serif', fontSize: 10,
                                    letterSpacing: 1.3, textTransform: 'uppercase',
                                    color: '#8F887E', margin: '0 0 4px',
                                  }}>
                                    Bring with you
                                  </p>
                                  <ul style={{ margin: '0 0 8px', paddingLeft: 16 }}>
                                    {r.documents_to_gather.map((d, j) => (
                                      <li key={j} style={{
                                        fontFamily: 'var(--font-body)', fontSize: 11,
                                        color: '#B0A99C', lineHeight: 1.6, marginBottom: 2,
                                      }}>{d}</li>
                                    ))}
                                  </ul>
                                </>
                              )}

                              {r.cost && (
                                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: ACCENT, lineHeight: 1.6, margin: '0 0 8px' }}>
                                  <strong>Cost: </strong>{r.cost}
                                </p>
                              )}
                              {r.note && (
                                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#B0A99C', lineHeight: 1.6, margin: '0 0 8px', fontStyle: 'italic' }}>
                                  {r.note}
                                </p>
                              )}
                              {r.verify_at && (
                                <a href={r.verify_at} target="_blank" rel="noopener noreferrer"
                                   style={{
                                     display: 'inline-block', fontFamily: 'var(--font-body)',
                                     fontSize: 11, color: ACCENT, textDecoration: 'underline',
                                     textUnderlineOffset: 2,
                                   }}>
                                  Official source ↗
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>

                  <p style={{
                    fontFamily: 'var(--font-body)', fontSize: 10, color: '#6E675E',
                    lineHeight: 1.55, margin: '10px 0 0',
                  }}>
                    {s.disclaimer}
                  </p>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  )
}
