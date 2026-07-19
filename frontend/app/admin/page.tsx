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
  fishbowl: Record<string, FishbowlRegion>
}

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
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API}/api/admin/stats`, { headers: { 'X-Admin-Key': key } })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || `Request failed (${res.status})`)
      }
      setStats(await res.json())
    } catch (e) {
      setStats(null)
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setLoading(false)
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 12 }}>
            {[
              { label: 'Total Cases', value: String(stats.total_cases) },
              { label: 'Paid', value: String(stats.paid_cases) },
              { label: 'Revenue (est.)', value: stats.revenue_estimate },
              { label: 'Today', value: String(stats.today) },
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
