'use client'

import { useState } from 'react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const GOLD = '#C9A84C'

interface FishbowlRegion {
  name: string
  current: number
  limit: number
  available: number
  utilization: number
}

interface AdminStats {
  total_cases: number
  paid_cases: number
  revenue_estimate: string
  today: number
  pending_manual: number
  fishbowl: Record<string, FishbowlRegion>
}

interface PendingPayment {
  session_id: string
  name: string
  email: string
  method: 'cashapp' | 'chime' | null
  confirmation: string | null
  requested_at: string | null
  amount: string
  letters_count: number
}

const METHOD_LABELS: Record<string, string> = { cashapp: 'Cash App', chime: 'Chime' }

const cardStyle: React.CSSProperties = {
  background: 'rgba(0,0,0,0.4)',
  border: `1px solid ${GOLD}22`,
  borderRadius: 6,
  padding: '18px 20px',
  marginBottom: 12,
}

export default function AdminPage() {
  const [key, setKey] = useState('')
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [pending, setPending] = useState<PendingPayment[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [releasing, setReleasing] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const headers = { 'X-Admin-Key': key }
      const [statsRes, pendingRes] = await Promise.all([
        fetch(`${API}/api/admin/stats`, { headers }),
        fetch(`${API}/api/admin/pending-payments`, { headers }),
      ])
      if (!statsRes.ok) {
        const body = await statsRes.json().catch(() => null)
        throw new Error(body?.detail || `Request failed (${statsRes.status})`)
      }
      setStats(await statsRes.json())
      if (pendingRes.ok) {
        const data = await pendingRes.json()
        setPending(Array.isArray(data.pending) ? data.pending : [])
      }
    } catch (e) {
      setStats(null)
      setPending([])
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  async function release(sessionId: string) {
    setReleasing(sessionId)
    setError('')
    try {
      const res = await fetch(`${API}/api/admin/release/${sessionId}`, {
        method: 'POST',
        headers: { 'X-Admin-Key': key },
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || `Release failed (${res.status})`)
      }
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Release failed')
    } finally {
      setReleasing(null)
    }
  }

  return (
    <div style={{ position: 'relative', zIndex: 5, maxWidth: 720, margin: '0 auto', padding: '2.5rem 1.25rem 5rem' }}>
      <Link href="/" style={{
        fontFamily: 'var(--font-cinzel), serif', fontSize: 12, letterSpacing: 2,
        textTransform: 'uppercase', color: '#8A8278', textDecoration: 'none',
      }}>
        &larr; Back to the Journey
      </Link>
      <h1 style={{
        fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '2rem',
        color: GOLD, letterSpacing: 2, margin: '18px 0 24px',
        textShadow: `0 0 24px ${GOLD}44`,
      }}>
        Admin
      </h1>

      <div style={cardStyle}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label style={{
              display: 'block', fontFamily: 'var(--font-cinzel), serif', fontSize: '0.72rem',
              color: GOLD, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 6,
            }}>
              Admin Key
            </label>
            <input
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && key && load()}
              placeholder="X-Admin-Key"
              style={{
                width: '100%', background: 'rgba(10,8,4,0.85)',
                border: `1px solid ${GOLD}33`, borderRadius: 4,
                padding: '10px 14px', color: '#F0EBE0',
                fontFamily: 'var(--font-body)', fontSize: 14, outline: 'none',
              }}
            />
          </div>
          <button
            onClick={load}
            disabled={!key || loading}
            style={{
              fontFamily: 'var(--font-heading)', fontSize: 12, letterSpacing: 2,
              textTransform: 'uppercase', color: '#050403',
              background: !key || loading ? 'rgba(100,100,100,0.3)' : `linear-gradient(135deg, ${GOLD}, #8B6914)`,
              padding: '11px 22px', borderRadius: 4, border: 'none',
              cursor: !key || loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Loading…' : 'Load Stats'}
          </button>
        </div>
        {error && (
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#FF5A5A', marginTop: 12, marginBottom: 0 }}>
            {error}
          </p>
        )}
      </div>

      {stats && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 12 }}>
            {[
              { label: 'Total Cases', value: String(stats.total_cases) },
              { label: 'Paid', value: String(stats.paid_cases) },
              { label: 'Revenue (est.)', value: stats.revenue_estimate },
              { label: 'Today', value: String(stats.today) },
              { label: 'Awaiting Release', value: String(stats.pending_manual ?? pending.length) },
            ].map((m) => (
              <div key={m.label} style={{
                background: 'rgba(0,0,0,0.4)', border: `1px solid ${GOLD}22`,
                borderRadius: 6, padding: '16px 12px', textAlign: 'center',
              }}>
                <div style={{ fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: 22, color: GOLD }}>
                  {m.value}
                </div>
                <div style={{
                  fontFamily: 'var(--font-body)', fontSize: 10, color: '#8A8278',
                  letterSpacing: 1.5, textTransform: 'uppercase', marginTop: 4,
                }}>
                  {m.label}
                </div>
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <h2 style={{
              fontFamily: 'var(--font-heading)', fontSize: 14, color: '#F0EBE0',
              letterSpacing: 1, marginBottom: 4,
            }}>
              Pending Manual Payments
            </h2>
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', marginTop: 0, marginBottom: 14 }}>
              Cash App / Chime payments waiting on verification. Match the code against the
              payment note in your app, then hit Release — it unlocks their letters, mails
              round 1, and emails the PDF packet.
            </p>
            {pending.length === 0 ? (
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278', margin: 0 }}>
                Nothing waiting. New requests show up here the moment a customer picks Cash App or Chime.
              </p>
            ) : (
              pending.map((p) => (
                <div key={p.session_id} style={{
                  display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap',
                  padding: '12px 14px', marginBottom: 8, borderRadius: 4,
                  border: `1px solid ${GOLD}33`, background: 'rgba(10,8,4,0.5)',
                }}>
                  <div style={{ flex: 1, minWidth: 180 }}>
                    <div style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: '#F0EBE0' }}>
                      {p.name}
                    </div>
                    <div style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', marginTop: 2 }}>
                      {p.email} &middot; {p.letters_count} letter{p.letters_count === 1 ? '' : 's'}
                      {p.requested_at && <> &middot; {new Date(p.requested_at + 'Z').toLocaleString()}</>}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontFamily: 'monospace', fontSize: 15, color: GOLD, letterSpacing: 2 }}>
                      {p.confirmation ?? '—'}
                    </div>
                    <div style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', marginTop: 2 }}>
                      {p.amount} via {p.method ? METHOD_LABELS[p.method] ?? p.method : '—'}
                    </div>
                  </div>
                  <button
                    onClick={() => release(p.session_id)}
                    disabled={releasing !== null}
                    style={{
                      fontFamily: 'var(--font-heading)', fontSize: 11, letterSpacing: 2,
                      textTransform: 'uppercase', color: '#050403',
                      background: releasing !== null ? 'rgba(100,100,100,0.3)' : 'linear-gradient(135deg, #5CFFCC, #1F8A6B)',
                      padding: '10px 18px', borderRadius: 4, border: 'none',
                      cursor: releasing !== null ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {releasing === p.session_id ? 'Releasing…' : 'Release'}
                  </button>
                </div>
              ))
            )}
          </div>

          <div style={cardStyle}>
            <h2 style={{
              fontFamily: 'var(--font-heading)', fontSize: 14, color: '#F0EBE0',
              letterSpacing: 1, marginBottom: 12,
            }}>
              Beta Regions (Fishbowl)
            </h2>
            {Object.entries(stats.fishbowl).map(([region, r]) => (
              <div key={region} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                fontFamily: 'var(--font-body)', fontSize: 13, marginBottom: 8,
              }}>
                <span style={{ width: 40, fontFamily: 'monospace', color: '#F0EBE0' }}>{region}</span>
                <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(100, r.utilization)}%`,
                    background: `${GOLD}AA`,
                    borderRadius: 4,
                  }} />
                </div>
                <span style={{ width: 80, textAlign: 'right', color: '#8A8278' }}>
                  {r.current}/{r.limit}
                </span>
                <span style={{ color: r.available > 0 ? '#5CFFCC' : '#FF5A5A' }}>
                  {r.available > 0 ? 'open' : 'full'}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
