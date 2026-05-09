'use client'

import { useState, useEffect, useCallback } from 'react'
import { useShojiNav } from '@/lib/shojiNav'

const FLASK = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'
const GOLD = '#C9A84C'
const ACCENT = '#C9A84C'

interface Stats {
  total: number
  paid: number
  pending: number
  revenue: number
  fu30: number
  fu60: number
  fu90: number
  referral_sources: Record<string, number>
}

interface Entry {
  session_id: string
  name: string
  phone: string
  email: string
  state: string
  referral_source: string
  confirmation: string
  status: string
  paid: boolean | number
  dispute_count: number
  follow_up_30_sent: number
  follow_up_60_sent: number
  follow_up_90_sent: number
  created_at: string
}

interface PipelineStats {
  total: number
  active: number
  in_30: number
  in_60: number
  in_90: number
  complete: number
  total_letters: number
  total_notifications: number
}

interface AgentLogEntry {
  agent: string
  action: string
  detail: string
  created_at: string
  session_id: string
}

interface PendingNotification {
  session_id: string
  name: string
  platform: string
  handle: string
  milestone_day: number
  days_since_dispatch: number
  confirmation: string
}

const REF_COLORS: Record<string, string> = {
  snapchat: '#FFFC00',
  tiktok: '#00f2ea',
  instagram: '#E1306C',
  direct_email: '#5CFFCC',
  other: '#8A8278',
}

export default function AdminPage() {
  const { navigateTo } = useShojiNav()
  const [authed, setAuthed] = useState(false)
  const [key, setKey] = useState('')
  const [authError, setAuthError] = useState('')
  const [stats, setStats] = useState<Stats | null>(null)
  const [entries, setEntries] = useState<Entry[]>([])
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [actionMsg, setActionMsg] = useState('')
  const [pipeline, setPipeline] = useState<PipelineStats | null>(null)
  const [agentLog, setAgentLog] = useState<AgentLogEntry[]>([])
  const [pendingDMs, setPendingDMs] = useState<PendingNotification[]>([])
  const [activeTab, setActiveTab] = useState<'cases' | 'pipeline' | 'notifications'>('cases')

  const fetchData = useCallback(async () => {
    try {
      const [subRes, pipeRes, dmRes] = await Promise.all([
        fetch(`${FLASK}/admin/api/submissions`, { credentials: 'include' }),
        fetch(`${FLASK}/admin/api/pipeline`, { credentials: 'include' }),
        fetch(`${FLASK}/admin/api/pending-notifications`, { credentials: 'include' }),
      ])
      if (subRes.ok) {
        const data = await subRes.json()
        setStats(data.stats)
        setEntries(data.entries || [])
      } else if (subRes.status === 302 || subRes.status === 401) {
        setAuthed(false)
        return
      }
      if (pipeRes.ok) {
        const pData = await pipeRes.json()
        setPipeline(pData.pipeline)
        setAgentLog(pData.agent_log || [])
      }
      if (dmRes.ok) {
        const dmData = await dmRes.json()
        setPendingDMs(dmData.pending || [])
      }
    } catch { /* server down */ }
  }, [])

  useEffect(() => {
    if (authed) fetchData()
  }, [authed, fetchData])

  async function handleLogin() {
    setAuthError('')
    try {
      const res = await fetch(`${FLASK}/admin/auth`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        credentials: 'include',
        body: `key=${encodeURIComponent(key)}`,
      })
      if (res.ok || res.redirected) {
        setAuthed(true)
      } else {
        setAuthError('Invalid admin key')
      }
    } catch {
      setAuthError('Cannot connect to server')
    }
  }

  async function approvePayment(sessionId: string) {
    setActionMsg('Approving payment...')
    try {
      const res = await fetch(`${FLASK}/admin/api/approve-payment`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      })
      const data = await res.json()
      setActionMsg(data.confirmed ? 'Payment approved' : data.error || 'Failed')
      fetchData()
    } catch { setActionMsg('Approve failed') }
    setTimeout(() => setActionMsg(''), 4000)
  }

  async function sendDMNotification(sessionId: string, day: number) {
    setActionMsg(`Marking ${day}-day DM as sent...`)
    try {
      const res = await fetch(`${FLASK}/api/watcher/notify`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, day }),
      })
      const data = await res.json()
      setActionMsg(data.ok ? 'Notification logged' : data.error || 'Failed')
      fetchData()
    } catch { setActionMsg('Failed') }
    setTimeout(() => setActionMsg(''), 4000)
  }

  async function runAction(endpoint: string, label: string) {
    setActionMsg(`Running ${label}...`)
    try {
      const res = await fetch(`${FLASK}${endpoint}`, { method: 'POST', credentials: 'include' })
      const data = await res.json()
      setActionMsg(`${label}: ${JSON.stringify(data)}`)
      fetchData()
    } catch {
      setActionMsg(`${label}: failed`)
    }
    setTimeout(() => setActionMsg(''), 4000)
  }

  function exportCSV() {
    const filtered = getFiltered()
    let csv = 'Name,Phone,Email,State,Source,Confirmation,Status,Disputes,Created\n'
    filtered.forEach((e) => {
      const vals = [e.name, e.phone, e.email, e.state, e.referral_source, e.confirmation,
        e.paid ? 'paid' : e.status, String(e.dispute_count || 0), e.created_at?.slice(0, 16)]
      csv += vals.map((v) => `"${(v || '').replace(/"/g, '""')}"`).join(',') + '\n'
    })
    const blob = new Blob([csv], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `credit_tool_cases_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
  }

  function getFiltered() {
    return entries.filter((e) => {
      const q = search.toLowerCase()
      const matchSearch = !q ||
        (e.name || '').toLowerCase().includes(q) ||
        (e.email || '').toLowerCase().includes(q) ||
        (e.phone || '').toLowerCase().includes(q) ||
        (e.confirmation || '').toLowerCase().includes(q)
      const matchStatus = !statusFilter ||
        (statusFilter === 'paid' ? e.paid : e.status === statusFilter)
      const matchSource = !sourceFilter || e.referral_source === sourceFilter
      return matchSearch && matchStatus && matchSource
    })
  }

  // Login screen
  if (!authed) {
    return (
      <>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/seascape.jpg" alt="" style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', objectFit: 'cover', zIndex: 0 }} />
        <div style={{
          position: 'relative', zIndex: 1, minHeight: '100vh',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            width: 360, padding: '2.5rem',
            background: 'rgba(10,6,2,0.85)', backdropFilter: 'blur(12px)',
            border: `1px solid ${GOLD}33`, borderRadius: 8,
            boxShadow: `0 0 60px rgba(201,168,76,0.15)`,
          }}>
            <h2 style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: '1.4rem', color: '#F0EBE0', letterSpacing: 2,
              textAlign: 'center', marginBottom: 6,
              textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 20px ${GOLD}55`,
            }}>
              Admin Access
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 12, color: '#8A8278',
              textAlign: 'center', marginBottom: 24, fontStyle: 'italic',
            }}>
              Enter admin key to proceed
            </p>
            <input
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              placeholder="Admin key"
              style={{
                width: '100%', padding: '12px 14px',
                background: 'rgba(10,8,4,0.85)',
                border: `1px solid ${GOLD}33`, borderRadius: 4,
                color: '#F0EBE0', fontFamily: 'var(--font-body)', fontSize: 14,
                outline: 'none', marginBottom: 16,
              }}
            />
            {authError && (
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#FF6B6B', marginBottom: 12, textAlign: 'center' }}>
                {authError}
              </p>
            )}
            <button
              onClick={handleLogin}
              style={{
                width: '100%', padding: '12px',
                fontFamily: 'var(--font-cinzel), serif', fontSize: 13,
                letterSpacing: 3, textTransform: 'uppercase',
                color: '#1A0A02',
                background: `linear-gradient(135deg, ${GOLD}, #8B6914)`,
                border: 'none', borderRadius: 4, cursor: 'pointer',
                boxShadow: `0 4px 20px ${GOLD}55`,
              }}
            >
              Enter
            </button>
            <button
              onClick={() => navigateTo('/')}
              style={{
                width: '100%', marginTop: 12, padding: '8px',
                fontFamily: 'var(--font-body)', fontSize: 11,
                color: '#8A8278', background: 'transparent',
                border: '1px solid rgba(138,130,120,0.2)', borderRadius: 4,
                cursor: 'pointer', letterSpacing: 1, textTransform: 'uppercase',
              }}
            >
              Back to App
            </button>
          </div>
        </div>
      </>
    )
  }

  const filtered = getFiltered()

  // Dashboard
  return (
    <div style={{ minHeight: '100vh', background: '#050403' }}>
      {/* Header */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 24px',
        borderBottom: `1px solid ${GOLD}22`,
        background: 'rgba(10,6,2,0.9)', backdropFilter: 'blur(12px)',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <h1 style={{
          fontFamily: 'var(--font-cinzel-decorative), serif',
          fontSize: '1.1rem', color: GOLD, letterSpacing: 3, margin: 0,
          textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 14px ${GOLD}55`,
        }}>
          Admin Dashboard
        </h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button onClick={() => navigateTo('/')} style={{
            fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
            background: 'transparent', border: 'none', cursor: 'pointer',
            letterSpacing: 1, textTransform: 'uppercase',
          }}>
            Back to App
          </button>
          <span style={{ fontSize: 10, color: '#5A5A5A' }}>AE Labs</span>
        </div>
      </header>

      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 20px' }}>
        {/* Stats row */}
        {stats && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
            {[
              { value: stats.total, label: 'Total Cases', color: GOLD },
              { value: stats.paid, label: 'Paid', color: '#5CFFCC' },
              { value: stats.pending, label: 'Pending', color: '#8CB4FF' },
              { value: `$${stats.revenue.toFixed(2)}`, label: 'Revenue', color: '#EF9F27' },
              { value: stats.fu30, label: '30-Day Sent', color: '#8CB4FF' },
              { value: stats.fu60, label: '60-Day Sent', color: '#EF9F27' },
              { value: stats.fu90, label: '90-Day Escalations', color: '#D94A3B' },
            ].map((s, i) => (
              <div key={i} style={{
                background: 'rgba(10,8,4,0.6)', border: `1px solid ${GOLD}15`,
                borderRadius: 8, padding: '20px 16px', textAlign: 'center',
              }}>
                <div style={{
                  fontFamily: 'var(--font-cinzel-decorative), serif',
                  fontSize: '1.8rem', color: s.color, lineHeight: 1,
                  textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 12px ${s.color}55`,
                }}>
                  {s.value}
                </div>
                <div style={{
                  fontFamily: 'var(--font-body)', fontSize: 9,
                  color: '#8A8278', letterSpacing: 1.5, textTransform: 'uppercase',
                  marginTop: 6,
                }}>
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Referral breakdown */}
        {stats?.referral_sources && Object.keys(stats.referral_sources).length > 0 && (
          <div style={{ display: 'flex', gap: 10, marginBottom: 24, flexWrap: 'wrap' }}>
            {Object.entries(stats.referral_sources).map(([src, count]) => (
              <div key={src} style={{
                background: 'rgba(10,8,4,0.6)', border: `1px solid ${(REF_COLORS[src] || '#8A8278')}22`,
                borderRadius: 6, padding: '12px 20px', textAlign: 'center', minWidth: 100,
              }}>
                <div style={{
                  fontFamily: 'var(--font-cinzel-decorative), serif',
                  fontSize: '1.4rem', color: REF_COLORS[src] || '#8A8278',
                  textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 10px ${REF_COLORS[src] || '#8A8278'}44`,
                }}>
                  {count}
                </div>
                <div style={{
                  fontFamily: 'var(--font-body)', fontSize: 9, color: '#8A8278',
                  letterSpacing: 1, textTransform: 'uppercase', marginTop: 4,
                }}>
                  {src.replace('_', ' ')}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pipeline stats */}
        {pipeline && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, marginBottom: 24 }}>
            {[
              { value: pipeline.active, label: 'Active', color: '#5CFFCC' },
              { value: pipeline.in_30, label: 'In 30-Day', color: '#8CB4FF' },
              { value: pipeline.in_60, label: 'In 60-Day', color: '#EF9F27' },
              { value: pipeline.in_90, label: 'In 90-Day', color: '#D94A3B' },
              { value: pipeline.complete, label: 'Complete', color: GOLD },
              { value: pipeline.total_letters, label: 'Letters Gen', color: '#5CFFCC' },
              { value: pipeline.total_notifications, label: 'Alerts Sent', color: '#8CB4FF' },
              { value: pendingDMs.length, label: 'Pending DMs', color: pendingDMs.length > 0 ? '#D94A3B' : '#8A8278' },
            ].map((s, i) => (
              <div key={i} style={{
                background: 'rgba(10,8,4,0.6)', border: `1px solid ${s.color}15`,
                borderRadius: 6, padding: '14px 10px', textAlign: 'center',
              }}>
                <div style={{ fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '1.4rem', color: s.color, textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 8px ${s.color}44` }}>{s.value}</div>
                <div style={{ fontFamily: 'var(--font-body)', fontSize: 8, color: '#8A8278', letterSpacing: 1, textTransform: 'uppercase', marginTop: 4 }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
          {[
            { label: 'Run Agents', endpoint: '/admin/api/run-agents' },
            { label: 'Run Follow-Ups', endpoint: '/admin/api/run-followups' },
            { label: 'Run 90-Day Purge', endpoint: '/admin/api/run-purge' },
          ].map((a) => (
            <button key={a.label} onClick={() => runAction(a.endpoint, a.label)} style={{
              fontFamily: 'var(--font-body)', fontSize: 11, letterSpacing: 1,
              textTransform: 'uppercase', color: '#8A8278',
              background: 'transparent', border: `1px solid ${GOLD}22`,
              borderRadius: 6, padding: '8px 16px', cursor: 'pointer',
            }}>
              {a.label}
            </button>
          ))}
          <button onClick={exportCSV} style={{
            fontFamily: 'var(--font-body)', fontSize: 11, letterSpacing: 1,
            textTransform: 'uppercase', color: GOLD,
            background: 'transparent', border: `1px solid ${GOLD}33`,
            borderRadius: 6, padding: '8px 16px', cursor: 'pointer',
          }}>
            Export CSV
          </button>
          <button onClick={fetchData} style={{
            fontFamily: 'var(--font-body)', fontSize: 11, letterSpacing: 1,
            textTransform: 'uppercase', color: '#8A8278',
            background: 'transparent', border: `1px solid ${GOLD}22`,
            borderRadius: 6, padding: '8px 16px', cursor: 'pointer',
          }}>
            Refresh
          </button>
          {actionMsg && (
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#5CFFCC' }}>
              {actionMsg}
            </span>
          )}
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: `1px solid ${GOLD}22` }}>
          {(['cases', 'pipeline', 'notifications'] as const).map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              fontFamily: 'var(--font-cinzel), serif', fontSize: 12, letterSpacing: 2,
              textTransform: 'uppercase', padding: '10px 24px', cursor: 'pointer',
              background: 'transparent', border: 'none',
              color: activeTab === tab ? GOLD : '#8A8278',
              borderBottom: activeTab === tab ? `2px solid ${GOLD}` : '2px solid transparent',
              textShadow: `0 0 8px currentColor, 0 0 20px currentColor${activeTab === tab ? `, 0 0 8px ${GOLD}44` : ''}`,
            }}>
              {tab}{tab === 'notifications' && pendingDMs.length > 0 ? ` (${pendingDMs.length})` : ''}
            </button>
          ))}
        </div>

        {activeTab === 'cases' && (<>
        {/* Search & filter */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
          <input
            type="text" placeholder="Search name, email, phone, confirmation..."
            value={search} onChange={(e) => setSearch(e.target.value)}
            style={{
              flex: 1, minWidth: 240, padding: '10px 14px',
              background: 'rgba(10,8,4,0.7)', border: `1px solid ${GOLD}22`,
              borderRadius: 6, color: '#F0EBE0', fontFamily: 'var(--font-body)',
              fontSize: 13, outline: 'none',
            }}
          />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{
            padding: '10px 14px', background: 'rgba(10,8,4,0.7)',
            border: `1px solid ${GOLD}22`, borderRadius: 6,
            color: '#F0EBE0', fontFamily: 'var(--font-body)', fontSize: 12, outline: 'none',
          }}>
            <option value="">All Statuses</option>
            <option value="started">Started</option>
            <option value="parsed">Parsed</option>
            <option value="reviewed">Reviewed</option>
            <option value="paid">Paid</option>
          </select>
          <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} style={{
            padding: '10px 14px', background: 'rgba(10,8,4,0.7)',
            border: `1px solid ${GOLD}22`, borderRadius: 6,
            color: '#F0EBE0', fontFamily: 'var(--font-body)', fontSize: 12, outline: 'none',
          }}>
            <option value="">All Sources</option>
            <option value="snapchat">Snapchat</option>
            <option value="tiktok">TikTok</option>
            <option value="instagram">Instagram</option>
            <option value="direct_email">Direct Email</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Cases table */}
        <div style={{
          background: 'rgba(10,8,4,0.5)', border: `1px solid ${GOLD}15`,
          borderRadius: 8, overflow: 'hidden',
        }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '16px 20px', borderBottom: `1px solid ${GOLD}15`,
          }}>
            <span style={{
              fontFamily: 'var(--font-cinzel), serif', fontSize: 15,
              color: GOLD, letterSpacing: 2,
              textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 10px ${GOLD}44`,
            }}>
              All Cases
            </span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278' }}>
              {filtered.length} of {entries.length}
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            {filtered.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 20px', color: '#8A8278', fontFamily: 'var(--font-body)', fontSize: 13 }}>
                {entries.length === 0 ? 'No cases yet.' : 'No matches.'}
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 1000 }}>
                <thead>
                  <tr>
                    {['Name', 'Phone', 'Email', 'State', 'Source', 'Confirmation', 'Status', 'Disputes', 'Follow-Ups', 'Created'].map((h) => (
                      <th key={h} style={{
                        textAlign: 'left', fontFamily: 'var(--font-body)',
                        fontSize: 9, letterSpacing: 1.5, textTransform: 'uppercase',
                        color: '#8A8278', padding: '10px 12px',
                        borderBottom: `1px solid ${GOLD}11`, whiteSpace: 'nowrap',
                      }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((e, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}
                      onMouseEnter={(ev) => { ev.currentTarget.style.background = `${GOLD}08` }}
                      onMouseLeave={(ev) => { ev.currentTarget.style.background = 'transparent' }}
                    >
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0', fontWeight: 600, whiteSpace: 'nowrap' }}>
                        {e.name || '---'}
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 12, whiteSpace: 'nowrap' }}>
                        {e.phone ? <a href={`tel:${e.phone}`} style={{ color: '#5CFFCC', textDecoration: 'none' }}>{e.phone}</a> : '---'}
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 12, whiteSpace: 'nowrap' }}>
                        {e.email ? <a href={`mailto:${e.email}`} style={{ color: '#5CFFCC', textDecoration: 'none' }}>{e.email}</a> : '---'}
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 12, color: '#F0EBE0' }}>
                        {e.state || '---'}
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                        {e.referral_source ? (
                          <span style={{
                            fontFamily: 'var(--font-body)', fontSize: 10, fontWeight: 600,
                            padding: '2px 8px', borderRadius: 10, letterSpacing: 0.5,
                            color: REF_COLORS[e.referral_source] || '#8A8278',
                            border: `1px solid ${(REF_COLORS[e.referral_source] || '#8A8278')}33`,
                            background: `${(REF_COLORS[e.referral_source] || '#8A8278')}11`,
                          }}>
                            {e.referral_source.replace('_', ' ')}
                          </span>
                        ) : '---'}
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'monospace', fontSize: 11, color: GOLD, whiteSpace: 'nowrap' }}>
                        {e.confirmation || '---'}
                      </td>
                      <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                        <span style={{
                          fontFamily: 'var(--font-body)', fontSize: 10, fontWeight: 700,
                          padding: '3px 10px', borderRadius: 12, letterSpacing: 0.5,
                          textTransform: 'uppercase',
                          ...(e.paid
                            ? { color: '#5CFFCC', border: '1px solid rgba(92,255,204,0.25)', background: 'rgba(92,255,204,0.08)' }
                            : e.status === 'pending_payment'
                              ? { color: '#EF9F27', border: '1px solid rgba(239,159,39,0.25)', background: 'rgba(239,159,39,0.06)' }
                              : e.status === 'reviewed'
                                ? { color: '#EF9F27', border: '1px solid rgba(239,159,39,0.25)', background: 'rgba(239,159,39,0.06)' }
                                : e.status === 'parsed'
                                  ? { color: '#8CB4FF', border: '1px solid rgba(140,180,255,0.2)', background: 'rgba(140,180,255,0.06)' }
                                  : { color: '#D94A3B', border: '1px solid rgba(217,74,59,0.2)', background: 'rgba(217,74,59,0.06)' }),
                        }}>
                          {e.paid ? 'Paid' : e.status || 'started'}
                        </span>
                        {e.status === 'pending_payment' && !e.paid && (
                          <button onClick={() => approvePayment(e.session_id)} style={{
                            marginLeft: 6, fontFamily: 'var(--font-body)', fontSize: 9,
                            padding: '2px 8px', borderRadius: 4, cursor: 'pointer',
                            color: '#5CFFCC', background: 'rgba(92,255,204,0.1)',
                            border: '1px solid rgba(92,255,204,0.3)',
                            letterSpacing: 0.5, textTransform: 'uppercase',
                          }}>
                            Approve
                          </button>
                        )}
                      </td>
                      <td style={{
                        padding: '10px 12px', textAlign: 'center',
                        fontFamily: 'var(--font-cinzel-decorative), serif',
                        fontSize: 16, color: GOLD,
                        textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 8px ${GOLD}44`,
                      }}>
                        {e.dispute_count || 0}
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 10, whiteSpace: 'nowrap' }}>
                        {e.follow_up_30_sent ? <span style={{ color: '#8CB4FF' }}>30d </span> : ''}
                        {e.follow_up_60_sent ? <span style={{ color: '#EF9F27' }}>60d </span> : ''}
                        {e.follow_up_90_sent ? <span style={{ color: '#D94A3B' }}>90d</span> : ''}
                        {!e.follow_up_30_sent && !e.follow_up_60_sent && !e.follow_up_90_sent && <span style={{ color: '#5A5A5A' }}>---</span>}
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', whiteSpace: 'nowrap' }}>
                        {e.created_at?.slice(0, 16) || '---'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
        </>)}

        {/* ═══ PIPELINE TAB ═══ */}
        {activeTab === 'pipeline' && (
          <div>
            {agentLog.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px', color: '#8A8278', fontFamily: 'var(--font-body)', fontSize: 13 }}>
                No agent activity yet. Agents run automatically every hour, or click &ldquo;Run Agents&rdquo; above.
              </div>
            ) : (
              <div style={{ background: 'rgba(10,8,4,0.5)', border: `1px solid ${GOLD}15`, borderRadius: 8, overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: `1px solid ${GOLD}15` }}>
                  <span style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 15, color: GOLD, letterSpacing: 2, textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 10px ${GOLD}44` }}>
                    Agent Activity Log
                  </span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 700 }}>
                    <thead>
                      <tr>
                        {['Agent', 'Action', 'Detail', 'Time'].map((h) => (
                          <th key={h} style={{ textAlign: 'left', fontFamily: 'var(--font-body)', fontSize: 9, letterSpacing: 1.5, textTransform: 'uppercase', color: '#8A8278', padding: '10px 12px', borderBottom: `1px solid ${GOLD}11` }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {agentLog.map((log, i) => {
                        const agentColor = log.agent === 'agent_30' ? '#8CB4FF' : log.agent === 'agent_60' ? '#EF9F27' : log.agent === 'agent_90' ? '#D94A3B' : GOLD
                        let detail = ''
                        try { const d = JSON.parse(log.detail); detail = `${d.confirmation || ''} | ${d.notify || ''}: ${d.handle || ''} | letters: ${d.letters || 0}` } catch { detail = log.detail || '' }
                        return (
                          <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                            <td style={{ padding: '10px 12px' }}>
                              <span style={{ fontFamily: 'var(--font-body)', fontSize: 11, fontWeight: 700, color: agentColor, letterSpacing: 1, textTransform: 'uppercase' }}>{log.agent}</span>
                            </td>
                            <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 12, color: '#F0EBE0' }}>{log.action}</td>
                            <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 11, color: '#A8A29A', maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis' }}>{detail}</td>
                            <td style={{ padding: '10px 12px', fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', whiteSpace: 'nowrap' }}>{log.created_at?.slice(0, 16)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══ NOTIFICATIONS TAB ═══ */}
        {activeTab === 'notifications' && (
          <div>
            {pendingDMs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px', color: '#8A8278', fontFamily: 'var(--font-body)', fontSize: 13 }}>
                No pending social media notifications. Email notifications are sent automatically.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <p style={{ fontFamily: 'var(--font-cinzel), serif', fontSize: 13, color: GOLD, letterSpacing: 2, marginBottom: 8 }}>
                  Pending Social Media DMs — Send these manually
                </p>
                {pendingDMs.map((dm, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 16, padding: '16px 18px',
                    background: 'rgba(10,8,4,0.5)', border: `1px solid ${(REF_COLORS[dm.platform] || '#8A8278')}33`,
                    borderRadius: 6,
                  }}>
                    <div style={{
                      flexShrink: 0, width: 48, height: 48, borderRadius: 8,
                      background: `${(REF_COLORS[dm.platform] || '#8A8278')}22`,
                      border: `1px solid ${(REF_COLORS[dm.platform] || '#8A8278')}44`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontFamily: 'var(--font-body)', fontSize: 11, fontWeight: 700,
                      color: REF_COLORS[dm.platform] || '#8A8278',
                      textTransform: 'uppercase', letterSpacing: 1,
                    }}>
                      {dm.milestone_day}d
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontFamily: 'var(--font-heading)', fontSize: 13, color: '#F0EBE0', margin: 0 }}>
                        {dm.name} &middot; <span style={{ color: REF_COLORS[dm.platform] || '#8A8278' }}>{dm.platform}</span>: {dm.handle}
                      </p>
                      <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', margin: '2px 0 0' }}>
                        Conf: {dm.confirmation} &middot; {dm.days_since_dispatch} days since dispatch &middot; {dm.milestone_day}-day follow-up due
                      </p>
                    </div>
                    <button onClick={() => sendDMNotification(dm.session_id, dm.milestone_day)} style={{
                      fontFamily: 'var(--font-body)', fontSize: 10, letterSpacing: 1,
                      textTransform: 'uppercase', padding: '8px 16px', borderRadius: 4,
                      cursor: 'pointer',
                      color: REF_COLORS[dm.platform] || '#8A8278',
                      background: `${(REF_COLORS[dm.platform] || '#8A8278')}15`,
                      border: `1px solid ${(REF_COLORS[dm.platform] || '#8A8278')}44`,
                    }}>
                      Mark Sent
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
