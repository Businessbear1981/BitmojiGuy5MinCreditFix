'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  adminLogin, adminLogout, setupOperator,
  getQueue, getConsumer, getStats, getNotifications,
  toggleRelease, releaseLetters, revokeLetters,
  markMailed, logResponse, addNote, getAuditLog,
  getUnmatchedPayments, logUnmatchedPayment,
} from '@/lib/adminApi'

const GOLD = '#C9A84C'
const BG = '#0A0806'
const CARD = 'rgba(14,10,4,0.95)'
const BORDER = 'rgba(201,168,76,0.2)'

type View = 'login' | 'setup' | 'queue' | 'consumer' | 'unmatched' | 'audit'

interface QueueItem {
  session_id: string; name: string; email: string; state: string
  confirmation: string; paid: boolean; paid_at: string
  dispute_count: number; days_since_action: number; letter_count: number
  referral_source: string; created_at: string
}

export default function OpConsolePage() {
  const [view, setView] = useState<View>('login')
  const [authed, setAuthed] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [totp, setTotp] = useState('')
  const [error, setError] = useState('')
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [search, setSearch] = useState('')
  const [stats, setStats] = useState<Record<string, number>>({})
  const [notifications, setNotifications] = useState<Record<string, unknown[]>>({})
  const [selectedSid, setSelectedSid] = useState('')
  const [consumerData, setConsumerData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)

  const loadQueue = useCallback(async () => {
    try {
      const res = await getQueue()
      if (res.ok) {
        const data = await res.json()
        setQueue(data.queue || [])
      } else if (res.status === 401) {
        setAuthed(false); setView('login')
      }
    } catch { /* offline */ }
  }, [])

  const loadStats = useCallback(async () => {
    try {
      const res = await getStats()
      if (res.ok) { const d = await res.json(); setStats(d.stats || {}) }
    } catch { /* */ }
  }, [])

  const loadNotifications = useCallback(async () => {
    try {
      const res = await getNotifications()
      if (res.ok) { const d = await res.json(); setNotifications(d.notifications || {}) }
    } catch { /* */ }
  }, [])

  useEffect(() => {
    if (authed) { loadQueue(); loadStats(); loadNotifications() }
  }, [authed, loadQueue, loadStats, loadNotifications])

  // ── LOGIN ─────────────────────────────────────────────────────────────────
  async function handleLogin() {
    setError('')
    const res = await adminLogin(username, password, totp)
    const data = await res.json()
    if (data.ok) {
      setAuthed(true); setView('queue')
    } else {
      setError(data.error || 'Login failed')
    }
  }

  async function handleSetup() {
    setError('')
    if (password.length < 8) { setError('Password must be 8+ characters'); return }
    const res = await setupOperator(username, password)
    const data = await res.json()
    if (data.ok) {
      alert(`Operator created!\n\nTOTP Secret: ${data.totp_secret || 'N/A (install pyotp)'}\n\nRecovery codes:\n${(data.recovery_codes || []).join('\n')}\n\nSave these now — they won't be shown again.`)
      setView('login')
    } else {
      setError(data.error || 'Setup failed')
    }
  }

  // ── RELEASE TOGGLE ────────────────────────────────────────────────────────
  async function handleToggle(sid: string, currentState: string) {
    const action = currentState === 'awaiting_release' ? 'release' : 'unrelease'
    if (action === 'unrelease' && !confirm('Revoke release? Consumer will lose download access.')) return
    await toggleRelease(sid, action)
    loadQueue()
  }

  // ── CONSUMER DETAIL ───────────────────────────────────────────────────────
  async function openConsumer(sid: string) {
    setLoading(true)
    setSelectedSid(sid)
    try {
      const res = await getConsumer(sid)
      if (res.ok) {
        const data = await res.json()
        setConsumerData(data)
        setView('consumer')
      }
    } catch { /* */ }
    setLoading(false)
  }

  // ── FILTER ────────────────────────────────────────────────────────────────
  const filtered = queue.filter((q) => {
    if (!search) return true
    const s = search.toLowerCase()
    return q.name.toLowerCase().includes(s) ||
           q.confirmation?.toLowerCase().includes(s) ||
           q.email?.toLowerCase().includes(s)
  })

  const stateColors: Record<string, string> = {
    awaiting_release: '#EF9F27',
    released: '#5CFFCC',
    mailed: '#8CB4FF',
    response_received: '#7F77DD',
    in_progress: '#8A8278',
    paid: '#EF9F27',
  }

  // ── RENDER ────────────────────────────────────────────────────────────────
  if (view === 'login' || view === 'setup') {
    return (
      <div style={{ minHeight: '100vh', background: BG, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: 380, padding: '2.5rem', background: CARD, border: `1px solid ${BORDER}`, borderRadius: 12 }}>
          <h1 style={{ fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '1.3rem', color: GOLD, textAlign: 'center', marginBottom: 24, textShadow: `0 0 8px ${GOLD}88` }}>
            Operator Console
          </h1>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)}
              style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 14, outline: 'none' }} />
            <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 14, outline: 'none' }} />
            {view === 'login' && (
              <input placeholder="TOTP Code (if enabled)" value={totp} onChange={(e) => setTotp(e.target.value)}
                style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 14, outline: 'none' }} />
            )}
            {error && <p style={{ color: '#FF6B6B', fontSize: 12, margin: 0 }}>{error}</p>}
            <button onClick={view === 'login' ? handleLogin : handleSetup}
              style={{ padding: '12px', background: `linear-gradient(135deg, ${GOLD}, #8B6914)`, color: '#050403', fontWeight: 700, fontSize: 14, border: 'none', borderRadius: 4, cursor: 'pointer', letterSpacing: 2, textTransform: 'uppercase' }}>
              {view === 'login' ? 'Login' : 'Create Operator'}
            </button>
            <button onClick={() => setView(view === 'login' ? 'setup' : 'login')}
              style={{ background: 'none', border: 'none', color: '#8A8278', fontSize: 11, cursor: 'pointer', textDecoration: 'underline' }}>
              {view === 'login' ? 'First time? Create operator account' : 'Back to login'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: BG, color: '#F0EBE0' }}>
      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <nav style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 24px', borderBottom: `1px solid ${BORDER}`, background: 'rgba(5,4,3,0.95)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '0.9rem', color: GOLD }}>Operator Console</span>
          <div style={{ display: 'flex', gap: 8 }}>
            {(['queue', 'unmatched', 'audit'] as View[]).map((v) => (
              <button key={v} onClick={() => { setView(v); if (v === 'queue') loadQueue() }}
                style={{ padding: '6px 14px', borderRadius: 4, border: `1px solid ${view === v ? GOLD + '88' : BORDER}`, background: view === v ? `${GOLD}15` : 'transparent', color: view === v ? GOLD : '#8A8278', fontSize: 11, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: 1 }}>
                {v === 'queue' ? 'Queue' : v === 'unmatched' ? 'Unmatched' : 'Audit Log'}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* Notification badges */}
          {(notifications.awaiting_release as unknown[] || []).length > 0 && (
            <span style={{ padding: '3px 8px', borderRadius: 10, background: '#EF9F27', color: '#050403', fontSize: 10, fontWeight: 700 }}>
              {(notifications.awaiting_release as unknown[]).length} awaiting
            </span>
          )}
          <span style={{ fontSize: 11, color: '#8A8278' }}>Total: {stats.total || 0} | Paid: {stats.paid || 0}</span>
          <button onClick={async () => { await adminLogout(); setAuthed(false); setView('login') }}
            style={{ padding: '6px 12px', borderRadius: 4, border: `1px solid ${BORDER}`, background: 'transparent', color: '#8A8278', fontSize: 11, cursor: 'pointer' }}>
            Logout
          </button>
        </div>
      </nav>

      <div style={{ padding: '1.5rem 2rem' }}>
        {/* ── QUEUE VIEW ────────────────────────────────────────────────── */}
        {view === 'queue' && (
          <>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center' }}>
              <input placeholder="Search by confirmation #, name, or email..." value={search} onChange={(e) => setSearch(e.target.value)}
                style={{ flex: 1, padding: '10px 14px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 14, outline: 'none' }} />
              <button onClick={loadQueue} style={{ padding: '10px 16px', background: `${GOLD}22`, border: `1px solid ${GOLD}44`, borderRadius: 4, color: GOLD, fontSize: 12, cursor: 'pointer' }}>
                Refresh
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {filtered.map((q) => (
                <div key={q.session_id} style={{
                  display: 'grid', gridTemplateColumns: '1fr 100px 100px 80px 80px 70px',
                  alignItems: 'center', gap: 12, padding: '14px 18px',
                  background: CARD, border: `1px solid ${BORDER}`, borderRadius: 6, cursor: 'pointer',
                }} onClick={() => openConsumer(q.session_id)}>
                  <div>
                    <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#F0EBE0' }}>{q.name || 'Unknown'}</p>
                    <p style={{ margin: 0, fontSize: 11, color: '#8A8278' }}>{q.email}</p>
                  </div>
                  <span style={{ fontFamily: 'monospace', fontSize: 13, color: GOLD, letterSpacing: 1.5 }}>
                    {q.confirmation || '—'}
                  </span>
                  <span style={{
                    fontSize: 10, textTransform: 'uppercase', letterSpacing: 1,
                    color: stateColors[q.state] || '#8A8278',
                    padding: '3px 8px', borderRadius: 3,
                    border: `1px solid ${(stateColors[q.state] || '#8A8278') + '44'}`,
                  }}>
                    {q.state.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: 11, color: '#8A8278' }}>{q.dispute_count} items</span>
                  <span style={{ fontSize: 11, color: '#8A8278' }}>{q.days_since_action}d ago</span>
                  {q.state === 'awaiting_release' ? (
                    <button onClick={(e) => { e.stopPropagation(); handleToggle(q.session_id, q.state) }}
                      style={{ padding: '6px 12px', borderRadius: 4, background: '#EF9F27', color: '#050403', fontSize: 11, fontWeight: 700, border: 'none', cursor: 'pointer' }}>
                      RELEASE
                    </button>
                  ) : q.state === 'released' ? (
                    <span style={{ fontSize: 10, color: '#5CFFCC', textAlign: 'center' }}>LIVE</span>
                  ) : (
                    <span style={{ fontSize: 10, color: '#8A8278', textAlign: 'center' }}>—</span>
                  )}
                </div>
              ))}
              {filtered.length === 0 && (
                <p style={{ textAlign: 'center', color: '#8A8278', padding: '2rem' }}>
                  {queue.length === 0 ? 'No consumers yet' : 'No results for search'}
                </p>
              )}
            </div>
          </>
        )}

        {/* ── CONSUMER DETAIL VIEW ──────────────────────────────────────── */}
        {view === 'consumer' && consumerData && (
          <ConsumerDetail
            data={consumerData}
            sid={selectedSid}
            onBack={() => { setView('queue'); loadQueue() }}
            onRefresh={() => openConsumer(selectedSid)}
          />
        )}

        {/* ── UNMATCHED PAYMENTS ────────────────────────────────────────── */}
        {view === 'unmatched' && <UnmatchedPaymentsPanel />}

        {/* ── AUDIT LOG ─────────────────────────────────────────────────── */}
        {view === 'audit' && <AuditLogPanel />}
      </div>

      {loading && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
          <p style={{ color: GOLD, fontSize: 14 }}>Loading...</p>
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// CONSUMER DETAIL COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

function ConsumerDetail({ data, sid, onBack, onRefresh }: {
  data: Record<string, unknown>; sid: string; onBack: () => void; onRefresh: () => void
}) {
  const consumer = data.consumer as Record<string, unknown> || {}
  const letters = (data.letters || []) as Record<string, unknown>[]
  const release = data.release as Record<string, unknown> | null
  const released = data.released as boolean
  const notes = (data.notes || []) as Record<string, unknown>[]
  const audit = (data.audit_log || []) as Record<string, unknown>[]
  const [noteText, setNoteText] = useState('')
  const [revokeOpen, setRevokeOpen] = useState(false)
  const [revokeReason, setRevokeReason] = useState('')
  const [revokeConfirm, setRevokeConfirm] = useState('')

  async function handleAddNote() {
    if (!noteText.trim()) return
    await addNote(sid, noteText)
    setNoteText('')
    onRefresh()
  }

  async function handleMarkMailed(letterId: number) {
    await markMailed(letterId)
    onRefresh()
  }

  async function handleLogResponse(letterId: number) {
    const outcome = prompt('Outcome (deleted / verified / modified / no_response):')
    if (!outcome || !['deleted', 'verified', 'modified', 'no_response'].includes(outcome)) return
    const responseNotes = prompt('Notes:') || ''
    await logResponse(letterId, outcome, responseNotes)
    onRefresh()
  }

  async function handleRevoke() {
    if (revokeConfirm !== 'REFUND AND REVOKE') { alert('Type "REFUND AND REVOKE" to confirm'); return }
    await revokeLetters(sid, revokeReason, '24.99', false)
    setRevokeOpen(false)
    onRefresh()
  }

  return (
    <div>
      <button onClick={onBack} style={{ marginBottom: 16, padding: '8px 16px', background: 'transparent', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#8A8278', fontSize: 12, cursor: 'pointer' }}>
        &larr; Back to Queue
      </button>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Identity */}
        <div style={{ padding: 20, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 8 }}>
          <h3 style={{ color: GOLD, fontSize: 12, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Consumer</h3>
          <p style={{ margin: '4px 0', fontSize: 14 }}>{consumer.name as string}</p>
          <p style={{ margin: '4px 0', fontSize: 12, color: '#8A8278' }}>{consumer.email as string}</p>
          <p style={{ margin: '4px 0', fontSize: 12, color: '#8A8278' }}>{consumer.phone as string}</p>
          <p style={{ margin: '4px 0', fontSize: 12, color: '#8A8278' }}>{consumer.state as string}</p>
          <p style={{ margin: '8px 0 0', fontSize: 11, color: '#5A5A5A' }}>Confirmation: <span style={{ fontFamily: 'monospace', color: GOLD }}>{consumer.confirmation as string || '—'}</span></p>
        </div>

        {/* Payment & Status */}
        <div style={{ padding: 20, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 8 }}>
          <h3 style={{ color: GOLD, fontSize: 12, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Status</h3>
          <p style={{ margin: '4px 0', fontSize: 13 }}>Status: <span style={{ color: released ? '#5CFFCC' : '#EF9F27' }}>{released ? 'RELEASED' : consumer.status as string}</span></p>
          <p style={{ margin: '4px 0', fontSize: 12, color: '#8A8278' }}>Paid: {consumer.paid ? 'Yes' : 'No'} {consumer.paid_at ? `(${(consumer.paid_at as string).slice(0, 10)})` : ''}</p>
          <p style={{ margin: '4px 0', fontSize: 12, color: '#8A8278' }}>Disputes: {consumer.dispute_count as number}</p>
          {released && !revokeOpen && (
            <button onClick={() => setRevokeOpen(true)} style={{ marginTop: 10, padding: '6px 12px', background: 'rgba(255,60,60,0.1)', border: '1px solid rgba(255,60,60,0.3)', borderRadius: 4, color: '#FF6B6B', fontSize: 11, cursor: 'pointer' }}>
              Refund & Revoke
            </button>
          )}
        </div>
      </div>

      {/* Revoke modal */}
      {revokeOpen && (
        <div style={{ padding: 20, background: 'rgba(255,60,60,0.05)', border: '1px solid rgba(255,60,60,0.3)', borderRadius: 8, marginBottom: 16 }}>
          <h3 style={{ color: '#FF6B6B', fontSize: 12, marginBottom: 10 }}>REFUND AND REVOKE ACCESS</h3>
          <input placeholder="Reason for refund" value={revokeReason} onChange={(e) => setRevokeReason(e.target.value)}
            style={{ width: '100%', padding: '8px 12px', marginBottom: 8, background: 'rgba(0,0,0,0.5)', border: '1px solid rgba(255,60,60,0.3)', borderRadius: 4, color: '#F0EBE0', fontSize: 13, outline: 'none' }} />
          <input placeholder='Type "REFUND AND REVOKE" to confirm' value={revokeConfirm} onChange={(e) => setRevokeConfirm(e.target.value)}
            style={{ width: '100%', padding: '8px 12px', marginBottom: 8, background: 'rgba(0,0,0,0.5)', border: '1px solid rgba(255,60,60,0.3)', borderRadius: 4, color: '#F0EBE0', fontSize: 13, outline: 'none' }} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={handleRevoke} style={{ padding: '8px 16px', background: '#FF4444', color: '#fff', border: 'none', borderRadius: 4, fontSize: 12, cursor: 'pointer' }}>Confirm Revoke</button>
            <button onClick={() => setRevokeOpen(false)} style={{ padding: '8px 16px', background: 'transparent', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#8A8278', fontSize: 12, cursor: 'pointer' }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Letters */}
      <div style={{ padding: 20, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 8, marginBottom: 16 }}>
        <h3 style={{ color: GOLD, fontSize: 12, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Letters ({letters.length})</h3>
        {letters.map((l, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0', borderBottom: `1px solid ${BORDER}` }}>
            <span style={{ fontSize: 12, color: '#F0EBE0', flex: 1 }}>{l.bureau as string} ({l.letter_type as string})</span>
            <span style={{ fontSize: 10, textTransform: 'uppercase', color: l.status === 'released' ? '#5CFFCC' : l.status === 'mailed' ? '#8CB4FF' : l.status === 'response_received' ? '#7F77DD' : '#8A8278' }}>
              {l.status as string}
            </span>
            {l.status === 'released' && (
              <button onClick={() => handleMarkMailed(l.id as number)} style={{ padding: '4px 8px', fontSize: 10, background: 'transparent', border: `1px solid ${BORDER}`, borderRadius: 3, color: '#8A8278', cursor: 'pointer' }}>Mark Mailed</button>
            )}
            {(l.status === 'mailed' || l.status === 'released') && (
              <button onClick={() => handleLogResponse(l.id as number)} style={{ padding: '4px 8px', fontSize: 10, background: 'transparent', border: `1px solid ${BORDER}`, borderRadius: 3, color: '#8A8278', cursor: 'pointer' }}>Log Response</button>
            )}
            {l.response_outcome ? <span style={{ fontSize: 10, color: '#7F77DD' }}>{`${l.response_outcome}`}</span> : null}
          </div>
        ))}
        {letters.length === 0 && <p style={{ color: '#8A8278', fontSize: 12 }}>No letters generated yet</p>}
      </div>

      {/* Operator Notes */}
      <div style={{ padding: 20, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 8, marginBottom: 16 }}>
        <h3 style={{ color: GOLD, fontSize: 12, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Operator Notes</h3>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <input placeholder="Add note..." value={noteText} onChange={(e) => setNoteText(e.target.value)}
            style={{ flex: 1, padding: '8px 12px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 13, outline: 'none' }} />
          <button onClick={handleAddNote} style={{ padding: '8px 14px', background: `${GOLD}22`, border: `1px solid ${GOLD}44`, borderRadius: 4, color: GOLD, fontSize: 12, cursor: 'pointer' }}>Add</button>
        </div>
        {notes.map((n, i) => (
          <div key={i} style={{ padding: '6px 0', borderBottom: `1px solid ${BORDER}` }}>
            <p style={{ margin: 0, fontSize: 12, color: '#F0EBE0' }}>{n.note as string}</p>
            <p style={{ margin: 0, fontSize: 10, color: '#5A5A5A' }}>{n.operator_username as string} — {(n.created_at as string).slice(0, 16)}</p>
          </div>
        ))}
      </div>

      {/* Audit Log */}
      <div style={{ padding: 20, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 8 }}>
        <h3 style={{ color: GOLD, fontSize: 12, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Audit Log</h3>
        {audit.map((a, i) => (
          <div key={i} style={{ padding: '4px 0', fontSize: 11, color: '#8A8278' }}>
            {(a.timestamp as string).slice(0, 19)} | {a.action as string} | {(a.details as string || '').slice(0, 60)}
          </div>
        ))}
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// UNMATCHED PAYMENTS PANEL
// ═══════════════════════════════════════════════════════════════════════════════

function UnmatchedPaymentsPanel() {
  const [payments, setPayments] = useState<Record<string, unknown>[]>([])
  const [form, setForm] = useState({ sender_name: '', amount: '', received_at: '', note_contents: '', operator_notes: '' })

  useEffect(() => { loadPayments() }, [])

  async function loadPayments() {
    const res = await getUnmatchedPayments()
    if (res.ok) { const d = await res.json(); setPayments(d.payments || []) }
  }

  async function handleLog() {
    await logUnmatchedPayment(form)
    setForm({ sender_name: '', amount: '', received_at: '', note_contents: '', operator_notes: '' })
    loadPayments()
  }

  return (
    <div>
      <h2 style={{ color: GOLD, fontSize: 14, letterSpacing: 2, marginBottom: 16 }}>UNMATCHED PAYMENTS</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr auto', gap: 8, marginBottom: 16 }}>
        <input placeholder="Sender" value={form.sender_name} onChange={(e) => setForm({ ...form, sender_name: e.target.value })}
          style={{ padding: '8px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 12, outline: 'none' }} />
        <input placeholder="Amount" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })}
          style={{ padding: '8px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 12, outline: 'none' }} />
        <input placeholder="Date received" value={form.received_at} onChange={(e) => setForm({ ...form, received_at: e.target.value })}
          style={{ padding: '8px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 12, outline: 'none' }} />
        <input placeholder="Note/memo contents" value={form.note_contents} onChange={(e) => setForm({ ...form, note_contents: e.target.value })}
          style={{ padding: '8px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 12, outline: 'none' }} />
        <input placeholder="Operator notes" value={form.operator_notes} onChange={(e) => setForm({ ...form, operator_notes: e.target.value })}
          style={{ padding: '8px', background: 'rgba(0,0,0,0.5)', border: `1px solid ${BORDER}`, borderRadius: 4, color: '#F0EBE0', fontSize: 12, outline: 'none' }} />
        <button onClick={handleLog} style={{ padding: '8px 14px', background: `${GOLD}22`, border: `1px solid ${GOLD}44`, borderRadius: 4, color: GOLD, fontSize: 12, cursor: 'pointer' }}>Log</button>
      </div>

      {payments.map((p, i) => (
        <div key={i} style={{ padding: '12px 16px', background: CARD, border: `1px solid ${BORDER}`, borderRadius: 6, marginBottom: 6 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <p style={{ margin: 0, fontSize: 13 }}>{p.sender_name as string} — ${p.amount as string}</p>
              <p style={{ margin: 0, fontSize: 11, color: '#8A8278' }}>Note: {p.note_contents as string || '(empty)'}</p>
            </div>
            <span style={{ fontSize: 10, textTransform: 'uppercase', color: p.status === 'unresolved' ? '#EF9F27' : '#5CFFCC' }}>{p.status as string}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// AUDIT LOG PANEL
// ═══════════════════════════════════════════════════════════════════════════════

function AuditLogPanel() {
  const [entries, setEntries] = useState<Record<string, unknown>[]>([])

  useEffect(() => {
    (async () => {
      const res = await getAuditLog()
      if (res.ok) { const d = await res.json(); setEntries(d.entries || []) }
    })()
  }, [])

  return (
    <div>
      <h2 style={{ color: GOLD, fontSize: 14, letterSpacing: 2, marginBottom: 16 }}>AUDIT LOG</h2>
      <div style={{ fontFamily: 'monospace', fontSize: 11 }}>
        {entries.map((e, i) => (
          <div key={i} style={{ padding: '4px 0', color: '#8A8278', borderBottom: `1px solid rgba(138,130,120,0.1)` }}>
            <span style={{ color: '#5A5A5A' }}>{(e.timestamp as string).slice(0, 19)}</span>
            {' '}<span style={{ color: GOLD }}>{e.operator_username as string || 'system'}</span>
            {' '}<span style={{ color: '#F0EBE0' }}>{e.action as string}</span>
            {' '}<span>{(e.details as string || '').slice(0, 80)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
