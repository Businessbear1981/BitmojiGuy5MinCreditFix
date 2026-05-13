const FLASK = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'

let _sessionId = ''
export function setApiSessionId(id: string) { _sessionId = id }
export function getApiSessionId() { return _sessionId }

function sessionHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const h: Record<string, string> = { ...extra }
  if (_sessionId) h['X-Session-ID'] = _sessionId
  return h
}

export async function submitIntake(data: object) {
  return fetch(`${FLASK}/api/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  })
}

export async function uploadDocument(file: File, type: 'id' | 'address' | 'report') {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('type', type)
  return fetch(`${FLASK}/api/upload`, { method: 'POST', credentials: 'include', headers: sessionHeaders(), body: fd })
}

export async function getDisputes() {
  return fetch(`${FLASK}/api/disputes`, { credentials: 'include', headers: sessionHeaders() })
}

export async function getLetters() {
  return fetch(`${FLASK}/api/letters`, { credentials: 'include', headers: sessionHeaders() })
}

export async function getLetterById(index: number) {
  return fetch(`${FLASK}/api/letters/${index}`, { credentials: 'include', headers: sessionHeaders() })
}

export async function createCheckout() {
  return fetch(`${FLASK}/api/create-checkout`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: '{}',
  })
}

export async function reviewDisputes(items: object[], customItems: object[]) {
  return fetch(`${FLASK}/api/review`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify({ items, custom_items: customItems }),
  })
}

export async function manualPay(method: string) {
  return fetch(`${FLASK}/api/manual-pay`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify({ method }),
  })
}

export async function getFollowupLetters(day: number) {
  return fetch(`${FLASK}/api/followup-letters/${day}`, { credentials: 'include', headers: sessionHeaders() })
}

export async function getWatcherStatus() {
  return fetch(`${FLASK}/api/watcher/status`, { credentials: 'include', headers: sessionHeaders() })
}

export async function subscribeWatcher(notify_method: string, notify_handle: string, payment_method: string) {
  return fetch(`${FLASK}/api/watcher/subscribe`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify({ notify_method, notify_handle, payment_method }),
  })
}

// ═════════════════════════════════════════════════════════════════════════════
// CREDIT REPORT HOOK
// ═════════════════════════════════════════════════════════════════════════════

export async function getCreditReportGuide() {
  return fetch(`${FLASK}/api/credit-report-guide`, { credentials: 'include', headers: sessionHeaders() })
}

export async function getCreditReportBureaus() {
  return fetch(`${FLASK}/api/credit-report-bureaus`, { credentials: 'include', headers: sessionHeaders() })
}

export async function parseCreditReport() {
  return fetch(`${FLASK}/api/parse-credit-report`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: '{}',
  })
}

export async function getCreditReportStatus() {
  return fetch(`${FLASK}/api/credit-report-status`, { credentials: 'include', headers: sessionHeaders() })
}

// ═════════════════════════════════════════════════════════════════════════════
// ADMIN RELEASE WORKFLOW
// ═════════════════════════════════════════════════════════════════════════════

export async function queueForRelease() {
  return fetch(`${FLASK}/api/admin/queue-for-release`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: '{}',
  })
}

export async function sendCertified(dayNumber: number = 0, mailClass: string = '') {
  return fetch(`${FLASK}/api/send-certified`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify({ dayNumber, mailClass }),
  })
}

export function getLettersUrl() {
  return `${FLASK}/api/letters`
}

// ═════════════════════════════════════════════════════════════════════════════
// ADMIN DASHBOARD
// ═════════════════════════════════════════════════════════════════════════════

export async function adminAuth(key: string) {
  return fetch(`${FLASK}/admin/auth`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `key=${encodeURIComponent(key)}`,
  })
}

export async function adminGetSubmissions() {
  return fetch(`${FLASK}/admin/api/submissions`, { credentials: 'include' })
}

export async function adminGetPipeline() {
  return fetch(`${FLASK}/admin/api/pipeline`, { credentials: 'include' })
}

export async function adminGetPendingNotifications() {
  return fetch(`${FLASK}/admin/api/pending-notifications`, { credentials: 'include' })
}

export async function adminApprovePayment(sessionId: string) {
  return fetch(`${FLASK}/admin/api/approve-payment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export async function adminNotifyClient(sessionId: string, day: number) {
  return fetch(`${FLASK}/api/watcher/notify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ session_id: sessionId, day }),
  })
}

export async function adminRunAction(endpoint: string) {
  return fetch(`${FLASK}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: '{}',
  })
}
