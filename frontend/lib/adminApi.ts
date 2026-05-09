const FLASK = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'
const BASE = `${FLASK}/op-console/api`

function post(path: string, body: object) {
  return fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
}

function get(path: string) {
  return fetch(`${BASE}${path}`, { credentials: 'include' })
}

// Auth
export const adminLogin = (username: string, password: string, totp_code: string) =>
  post('/login', { username, password, totp_code })
export const adminLogout = () => post('/logout', {})
export const setupOperator = (username: string, password: string) =>
  post('/setup-operator', { username, password })

// Queue & consumers
export const getQueue = () => get('/queue')
export const getConsumer = (sid: string) => get(`/consumer/${sid}`)
export const getStats = () => get('/stats')
export const getNotifications = () => get('/notifications')

// Actions
export const toggleRelease = (session_id: string, action: 'release' | 'unrelease') =>
  post('/toggle-release', { session_id, action })
export const releaseLetters = (session_id: string, payment_amount: string, payment_method: string, transaction_reference: string) =>
  post('/release', { session_id, payment_amount, payment_method, transaction_reference })
export const revokeLetters = (session_id: string, reason: string, refund_amount: string, already_mailed: boolean) =>
  post('/revoke', { session_id, confirm_text: 'REFUND AND REVOKE', reason, refund_amount, already_mailed })
export const markMailed = (letter_id: number) =>
  post('/mark-mailed', { letter_id })
export const logResponse = (letter_id: number, outcome: string, notes: string) =>
  post('/log-response', { letter_id, outcome, notes })
export const addNote = (session_id: string, note: string) =>
  post('/add-note', { session_id, note })
export const getAuditLog = (session_id?: string) =>
  get(`/audit-log${session_id ? `?session_id=${session_id}` : ''}`)

// Unmatched payments
export const getUnmatchedPayments = () => get('/unmatched-payments')
export const logUnmatchedPayment = (data: { sender_name: string; amount: string; received_at: string; note_contents: string; operator_notes: string }) =>
  post('/unmatched-payments/log', data)
export const linkUnmatchedPayment = (payment_id: number, session_id: string) =>
  post(`/unmatched-payments/${payment_id}/link`, { session_id })
export const resolveUnmatchedPayment = (payment_id: number, status: string, reason: string) =>
  post(`/unmatched-payments/${payment_id}/resolve`, { status, reason })
