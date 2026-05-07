'use client'

import { useState, useEffect } from 'react'
import { AlertCircle, CheckCircle, XCircle, Clock, Mail } from 'lucide-react'

const FLASK = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'
const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_KEY ?? 'ae-admin-2025'
const GOLD = '#C9A84C'

interface PendingSubmission {
  session_id: string
  user_name: string
  queued_at: string
  letter_count: number
}

interface ReleaseLogEntry {
  timestamp: string
  action: string
  session_id: string
  user_name: string
  admin_id?: string
  reason?: string
}

export function ReleaseQueue() {
  const [pending, setPending] = useState<PendingSubmission[]>([])
  const [log, setLog] = useState<ReleaseLogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'pending' | 'log'>('pending')
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({})
  const [showRejectForm, setShowRejectForm] = useState<string | null>(null)

  // Fetch pending queue
  const fetchPendingQueue = async () => {
    try {
      const res = await fetch(`${FLASK}/api/admin/pending-queue`, {
        headers: { 'X-Admin-Key': ADMIN_KEY },
      })
      if (res.ok) {
        const data = await res.json()
        setPending(data.pending || [])
      }
    } catch (err) {
      console.error('Error fetching pending queue:', err)
    }
  }

  // Fetch release log
  const fetchReleaseLog = async () => {
    try {
      const res = await fetch(`${FLASK}/api/admin/release-log?limit=50`, {
        headers: { 'X-Admin-Key': ADMIN_KEY },
      })
      if (res.ok) {
        const data = await res.json()
        setLog(data.log || [])
      }
    } catch (err) {
      console.error('Error fetching release log:', err)
    }
  }

  // Approve release
  const handleApprove = async (sessionId: string) => {
    setLoading(true)
    try {
      const res = await fetch(`${FLASK}/api/admin/approve-release`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': ADMIN_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          admin_id: 'admin-user',
        }),
      })
      if (res.ok) {
        setPending(pending.filter((p) => p.session_id !== sessionId))
        await fetchReleaseLog()
      }
    } catch (err) {
      console.error('Error approving release:', err)
    } finally {
      setLoading(false)
    }
  }

  // Reject release
  const handleReject = async (sessionId: string) => {
    setLoading(true)
    try {
      const res = await fetch(`${FLASK}/api/admin/reject-release`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': ADMIN_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          admin_id: 'admin-user',
          reason: rejectReason[sessionId] || 'No reason provided',
        }),
      })
      if (res.ok) {
        setPending(pending.filter((p) => p.session_id !== sessionId))
        setShowRejectForm(null)
        setRejectReason({})
        await fetchReleaseLog()
      }
    } catch (err) {
      console.error('Error rejecting release:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPendingQueue()
    fetchReleaseLog()
    const interval = setInterval(() => {
      fetchPendingQueue()
      fetchReleaseLog()
    }, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  return (
    <div
      style={{
        background: 'rgba(12,8,4,0.9)',
        border: `1px solid ${GOLD}`,
        borderRadius: 8,
        padding: '2rem',
        color: '#F0EBE0',
      }}
    >
      <h2 style={{ color: GOLD, marginBottom: '1.5rem', fontSize: '1.5rem' }}>
        📮 Admin Release Queue
      </h2>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button
          onClick={() => setActiveTab('pending')}
          style={{
            padding: '0.75rem 1.5rem',
            background: activeTab === 'pending' ? GOLD : 'transparent',
            color: activeTab === 'pending' ? '#0A0804' : GOLD,
            border: `1px solid ${GOLD}`,
            borderRadius: 4,
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          ⏳ Pending ({pending.length})
        </button>
        <button
          onClick={() => setActiveTab('log')}
          style={{
            padding: '0.75rem 1.5rem',
            background: activeTab === 'log' ? GOLD : 'transparent',
            color: activeTab === 'log' ? '#0A0804' : GOLD,
            border: `1px solid ${GOLD}`,
            borderRadius: 4,
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          📋 Activity Log
        </button>
      </div>

      {/* Pending Queue */}
      {activeTab === 'pending' && (
        <div>
          {pending.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '2rem',
                color: '#999',
              }}
            >
              ✅ No pending submissions. All caught up!
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {pending.map((sub) => (
                <div
                  key={sub.session_id}
                  style={{
                    background: 'rgba(201,168,76,0.1)',
                    border: `1px solid rgba(201,168,76,0.3)`,
                    borderRadius: 6,
                    padding: '1.5rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                    <div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: GOLD }}>
                        {sub.user_name}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#999', marginTop: '0.25rem' }}>
                        Session: {sub.session_id.slice(0, 8)}...
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#999', marginTop: '0.25rem' }}>
                        📧 {sub.letter_count} letter{sub.letter_count !== 1 ? 's' : ''} ready to send
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.5rem' }}>
                        Queued: {new Date(sub.queued_at).toLocaleString()}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                      <button
                        onClick={() => handleApprove(sub.session_id)}
                        disabled={loading}
                        style={{
                          padding: '0.75rem 1.25rem',
                          background: '#4CAF50',
                          color: 'white',
                          border: 'none',
                          borderRadius: 4,
                          cursor: loading ? 'not-allowed' : 'pointer',
                          opacity: loading ? 0.6 : 1,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          fontWeight: 'bold',
                        }}
                      >
                        <CheckCircle size={16} />
                        Approve
                      </button>
                      <button
                        onClick={() => setShowRejectForm(sub.session_id)}
                        disabled={loading}
                        style={{
                          padding: '0.75rem 1.25rem',
                          background: '#f44336',
                          color: 'white',
                          border: 'none',
                          borderRadius: 4,
                          cursor: loading ? 'not-allowed' : 'pointer',
                          opacity: loading ? 0.6 : 1,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          fontWeight: 'bold',
                        }}
                      >
                        <XCircle size={16} />
                        Reject
                      </button>
                    </div>
                  </div>

                  {/* Reject form */}
                  {showRejectForm === sub.session_id && (
                    <div
                      style={{
                        marginTop: '1rem',
                        padding: '1rem',
                        background: 'rgba(244,67,54,0.1)',
                        borderRadius: 4,
                        borderLeft: '3px solid #f44336',
                      }}
                    >
                      <textarea
                        placeholder="Reason for rejection..."
                        value={rejectReason[sub.session_id] || ''}
                        onChange={(e) =>
                          setRejectReason({
                            ...rejectReason,
                            [sub.session_id]: e.target.value,
                          })
                        }
                        style={{
                          width: '100%',
                          minHeight: '80px',
                          padding: '0.75rem',
                          background: 'rgba(10,8,4,0.8)',
                          border: '1px solid #f44336',
                          borderRadius: 4,
                          color: '#F0EBE0',
                          fontFamily: 'monospace',
                          fontSize: '0.9rem',
                          marginBottom: '0.75rem',
                        }}
                      />
                      <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <button
                          onClick={() => handleReject(sub.session_id)}
                          disabled={loading}
                          style={{
                            padding: '0.5rem 1rem',
                            background: '#f44336',
                            color: 'white',
                            border: 'none',
                            borderRadius: 4,
                            cursor: 'pointer',
                            fontWeight: 'bold',
                          }}
                        >
                          Confirm Rejection
                        </button>
                        <button
                          onClick={() => {
                            setShowRejectForm(null)
                            setRejectReason({})
                          }}
                          style={{
                            padding: '0.5rem 1rem',
                            background: 'transparent',
                            color: '#999',
                            border: '1px solid #999',
                            borderRadius: 4,
                            cursor: 'pointer',
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Activity Log */}
      {activeTab === 'log' && (
        <div>
          {log.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '2rem',
                color: '#999',
              }}
            >
              No activity yet
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {log.map((entry, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '1rem',
                    background: 'rgba(201,168,76,0.05)',
                    border: '1px solid rgba(201,168,76,0.15)',
                    borderRadius: 4,
                    fontSize: '0.9rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div>
                      <div style={{ color: GOLD, fontWeight: 'bold' }}>
                        {entry.action.replace(/_/g, ' ').toUpperCase()}
                      </div>
                      <div style={{ color: '#999', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                        {entry.user_name} • {entry.session_id.slice(0, 8)}...
                      </div>
                      {entry.reason && (
                        <div style={{ color: '#f44336', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                          Reason: {entry.reason}
                        </div>
                      )}
                    </div>
                    <div style={{ color: '#666', fontSize: '0.85rem', whiteSpace: 'nowrap' }}>
                      {new Date(entry.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
