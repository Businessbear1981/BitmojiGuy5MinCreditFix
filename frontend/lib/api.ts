// AE 5-Min Credit Fix — Typed client for the FastAPI backend (/api/case/*).
//
// The journey pages consume raw fetch Responses (`res.ok` / `res.json()`), so
// every function here keeps that contract: real Responses are passed through
// (or re-synthesized when the body was already read), and flows the FastAPI
// backend doesn't support return synthesized JSON Responses so the pages can
// render a graceful state without visual changes.

import { BUCKET_LABELS } from './types'
import type { CaseStatus, GeneratedLetter, MailTracking, Suggestion } from './types'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ═════════════════════════════════════════════════════════════════════════════
// SESSION PERSISTENCE
// ═════════════════════════════════════════════════════════════════════════════

// Session continuity: the FastAPI backend keys all state off the session id in
// the URL path. We persist the id to localStorage so it survives full page
// loads: the Stripe checkout redirect back to /gate and any mid-journey
// refresh. Rehydrate synchronously on module load (SSR-guarded).
const SESSION_KEY = 'cf_session_id'
const SUGGESTIONS_KEY = 'cf_suggestions'

let _sessionId = ''
if (typeof window !== 'undefined') {
  try { _sessionId = window.localStorage.getItem(SESSION_KEY) ?? '' } catch { /* storage blocked */ }
}

export function setApiSessionId(id: string) {
  _sessionId = id
  if (typeof window !== 'undefined') {
    try { window.localStorage.setItem(SESSION_KEY, id) } catch { /* storage blocked */ }
  }
}

export function getApiSessionId() { return _sessionId }

export function clearApiSessionId() {
  _sessionId = ''
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.removeItem(SESSION_KEY)
      window.localStorage.removeItem(SUGGESTIONS_KEY)
    } catch { /* storage blocked */ }
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// HELPERS
// ═════════════════════════════════════════════════════════════════════════════

/** Build a JSON Response so callers can keep using res.ok / res.json(). */
function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Extract a human-readable message from a FastAPI error body. */
function detailMessage(data: unknown, fallback: string): string {
  if (data && typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
  }
  return fallback
}

async function readJson(res: Response): Promise<Record<string, unknown>> {
  try { return await res.json() } catch { return {} }
}

// Parsed dispute suggestions arrive in the upload response; the koi-pond page
// fetches them later via getDisputes(), so cache them across navigations.
function cacheSuggestions(suggestions: Suggestion[]) {
  if (typeof window === 'undefined') return
  try { window.localStorage.setItem(SUGGESTIONS_KEY, JSON.stringify(suggestions)) } catch { /* storage blocked */ }
}

/**
 * How much a parsed report is worth arguing.
 *
 * An item that names an account number is worth more than one that cannot,
 * because the bureau can look the first one up. Counting both means a report
 * with more detail wins over a report with more rows.
 */
function reportStrength(suggestions: Suggestion[]): number {
  const identified = suggestions.filter((s) => {
    const acct = String((s as { account?: unknown }).account ?? '').trim()
    return acct.length >= 4 && /\d/.test(acct)
  }).length
  return identified * 2 + suggestions.length
}

/** Which bureau a parse describes, by majority of its items' targets. */
function bureauOf(suggestions: Suggestion[]): string {
  const tally = new Map<string, number>()
  for (const s of suggestions) {
    const t = String((s as { target?: unknown }).target ?? '').trim()
    if (t) tally.set(t, (tally.get(t) ?? 0) + 1)
  }
  let best = ''
  let seen = 0
  for (const [name, n] of tally) if (n > seen) { best = name; seen = n }
  return best
}

/**
 * Keep the strongest parse *per bureau*, and keep every bureau.
 *
 * Two separate mistakes lived here. First the cache was a plain overwrite, so
 * uploading three reports left whichever went in last — an Experian parse of
 * 52 items replaced by a TransUnion parse of 20. Replacing that with a single
 * strongest-wins cache fixed the junk but then threw Equifax away, and since a
 * letter is only ever addressed to the bureau whose file it was read from,
 * that silently reduced a three-bureau product to one letter.
 *
 * A consumer disputing with Equifax needs the items Equifax reports, so each
 * bureau keeps its own parse and only a stronger parse of the *same* bureau
 * replaces it. Returns whether the incoming parse was adopted.
 */
function cacheReportByBureau(suggestions: Suggestion[]): boolean {
  if (!suggestions.length) return false
  const bureau = bureauOf(suggestions)
  if (!bureau) return false

  const existing = loadSuggestions()
  const sameBureau = existing.filter((s) => bureauOf([s]) === bureau)
  if (sameBureau.length && reportStrength(suggestions) <= reportStrength(sameBureau)) {
    return false
  }
  const others = existing.filter((s) => bureauOf([s]) !== bureau)
  cacheSuggestions([...others, ...suggestions])
  return true
}

function loadSuggestions(): Suggestion[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(SUGGESTIONS_KEY)
    return raw ? (JSON.parse(raw) as Suggestion[]) : []
  } catch {
    return []
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// INTAKE — terms consent + case creation
// ═════════════════════════════════════════════════════════════════════════════

export interface IntakeData {
  name: string
  email: string
  phone: string
  // Street line only. The mail carrier needs city, state and ZIP as their own
  // fields — recovering them by splitting a free-text address put the unit
  // number in the city field and dropped the mailing silently.
  address: string
  city: string
  state: string
  zip: string
  dob: string
  ssn_last4: string
}

export async function submitIntake(data: IntakeData): Promise<Response> {
  // Consent gate: the backend refuses case creation without a terms token.
  const termsRes = await fetch(`${API}/api/terms/accept`, { method: 'POST' })
  const termsData = await readJson(termsRes)
  if (!termsRes.ok || !termsData.terms_token) {
    return jsonResponse(
      { error: detailMessage(termsData, 'Could not record terms acceptance — please try again.') },
      termsRes.ok ? 500 : termsRes.status,
    )
  }

  const res = await fetch(`${API}/api/case`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Terms-Token': String(termsData.terms_token),
    },
    body: JSON.stringify(data),
  })
  const caseData = await readJson(res)
  if (res.ok && typeof caseData.session_id === 'string') {
    // New case: reset any stale state from a previous session.
    try { window.localStorage.removeItem(SUGGESTIONS_KEY) } catch { /* storage blocked */ }
    setApiSessionId(caseData.session_id)
  }
  if (!res.ok) {
    return jsonResponse({ error: detailMessage(caseData, 'Could not create your case — please try again.') }, res.status)
  }
  return jsonResponse(caseData, res.status)
}

// ═════════════════════════════════════════════════════════════════════════════
// DOCUMENT UPLOAD — parsing happens server-side on upload
// ═════════════════════════════════════════════════════════════════════════════

export async function uploadDocument(file: File, type: 'id' | 'address' | 'report'): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ error: 'No active session — please complete the intake first.' }, 400)
  }
  const fd = new FormData()
  fd.append('file', file)
  // The slot knows what this document is and the server cannot guess. Omitting
  // it meant an ID and a bank statement were both parsed as credit reports.
  fd.append('doc_type', type)
  const res = await fetch(`${API}/api/case/${_sessionId}/upload`, { method: 'POST', body: fd })
  const data = await readJson(res)
  if (res.ok && type === 'report' && Array.isArray(data.suggestions)) {
    data.report_adopted = cacheReportByBureau(data.suggestions as Suggestion[])
    data.items_in_use = loadSuggestions().length
  }
  if (!res.ok) {
    return jsonResponse({ error: detailMessage(data, 'Upload failed — please try again.') }, res.status)
  }
  return jsonResponse(data, res.status)
}

// ═════════════════════════════════════════════════════════════════════════════
// DISPUTES — suggestions come from the upload parse; confirm + generate letters
// ═════════════════════════════════════════════════════════════════════════════

/** Shape the koi-pond page renders. */
interface DisputeItemView {
  // Position in the cached suggestion list. The review screen round-trips
  // this back so each authorised row maps to the item the customer actually
  // ticked. It used to match on the display string `account || target`, and
  // the parser writes "Unknown" into `account` for nearly every item — so
  // every row carried the same key and `.find()` returned the first
  // suggestion every time. Twelve selected accounts became eleven copies of
  // one wrong creditor, mailed to three bureaus.
  suggestion_index: number
  creditor: string
  account_number: string
  type: string
  amount: string
  date: string
  dispute: boolean
  dispute_box: string
  dispute_label: string
  label?: string
}

function toDisputeView(s: Suggestion, index: number): DisputeItemView {
  return {
    suggestion_index: index,
    // Prefer the furnisher name over the account number for display: the
    // parser writes "Unknown" into `account` for most items, which made every
    // row on the review screen read "Unknown".
    // The furnisher is who reports the item; `target` is only the bureau the
    // letter goes to, so prefer the furnisher when the parser found one.
    creditor: s.furnisher || s.target || s.account,
    account_number: s.account && !/^unknown$/i.test(s.account) ? s.account : '',
    type: s.type,
    // `amount` is an exact decimal string and "" means the report showed no
    // figure. A null check alone rendered a bare "$" on every such row.
    amount: s.amount ? `$${s.amount}` : '',
    date: s.opened ?? '',
    dispute: true,
    dispute_box: s.bucket,
    dispute_label: BUCKET_LABELS[s.bucket] ?? s.bucket,
    label: s.reason,
  }
}

export async function getDisputes(): Promise<Response> {
  return jsonResponse({
    ok: true,
    dispute_items: loadSuggestions().map((s, i) => toDisputeView(s, i)),
  })
}

interface ReviewedItem {
  suggestion_index?: number
  type?: string
  text?: string
  creditor?: string
  account_number?: string
  amount?: string
}

export async function reviewDisputes(
  items: object[],
  customItems: object[],
  acknowledgements?: Record<string, boolean>,
): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ ok: false, error: 'No active session — please complete the intake first.' }, 400)
  }

  // Map the page's selection back to the backend's DisputeItem shape using the
  // cached parser suggestions (the page round-trips `creditor` = suggestion.account).
  const suggestions = loadSuggestions()
  const confirmed = [...(items as ReviewedItem[]), ...(customItems as ReviewedItem[])].map((item) => {
    const match = typeof item.suggestion_index === 'number'
      ? suggestions[item.suggestion_index]
      : undefined
    if (match) {
      // Pass the parser's whole reading through, not a six-field summary of
      // it. Dropping `furnisher` printed "Account Name: Experian" on every
      // item, and dropping `categories` sent items to the letter's fallback
      // section instead of the violation theory the parser had already
      // matched. The server validates each field; unknown values are dropped
      // there, so forwarding them is safe.
      const m = match as Suggestion & Record<string, unknown>
      return {
        type: match.type,
        target: match.target,
        account: match.account,
        amount: match.amount,
        opened: match.opened,
        reason: match.reason,
        bucket: m.bucket ?? '',
        furnisher: m.furnisher ?? '',
        dofd: m.dofd ?? null,
        original_creditor: m.original_creditor ?? '',
        highest_balance: m.highest_balance ?? null,
        falloff_status: m.falloff_status ?? '',
        categories: m.categories ?? [],
      }
    }
    // Custom / unmatched item: dispute it directly with the creditor named.
    return {
      type: 'creditor' as const,
      target: item.creditor || 'Creditor',
      account: item.account_number || item.creditor || item.text || 'Unknown account',
      amount: null,
      opened: null,
      reason: item.text || 'This item is inaccurate and I dispute it.',
    }
  })

  const res = await fetch(`${API}/api/case/${_sessionId}/disputes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items: confirmed }),
  })
  const data = await readJson(res)
  if (!res.ok) {
    return jsonResponse({ ok: false, error: detailMessage(data, 'Could not save your disputes.') }, res.status)
  }

  // Record the consumer's acknowledgements before asking for letters. The
  // backend returns 428 without them, which is what dead-ended this step:
  // the disputes above were saved and the letter call then failed, so every
  // retry appended another copy of the item list.
  if (acknowledgements) {
    const ackRes = await acknowledgeDisclosures(acknowledgements)
    if (!ackRes.ok) {
      const ackData = await readJson(ackRes)
      return jsonResponse(
        { ok: false, error: ackData.error || 'Could not record your acknowledgements.' },
        ackRes.status,
      )
    }
  }

  // Generate the letters now so the garden page can simply fetch them.
  const genRes = await fetch(`${API}/api/case/${_sessionId}/letters`, { method: 'POST' })
  const genData = await readJson(genRes)
  if (!genRes.ok) {
    return jsonResponse({ ok: false, error: detailMessage(genData, 'Could not generate letters.') }, genRes.status)
  }

  return jsonResponse({ ok: true, items_count: data.items_count, total: genData.total })
}

// ═════════════════════════════════════════════════════════════════════════════
// DISCLOSURES — the consent gate in front of letter generation
// ═════════════════════════════════════════════════════════════════════════════

// POST /letters returns 428 until every required acknowledgement is recorded.
// These are CROA-relevant affirmations, so the consumer has to tick them
// themselves — nothing here may default them to true or send them unread.

export interface DisclosureSection {
  id: string
  heading: string
  body: string
}

export interface DisclosureAck {
  id: string
  label: string
}

export interface DisclosurePayload {
  version: string
  sections: DisclosureSection[]
  acknowledgements: DisclosureAck[]
  fine_print: string
  fine_print_short: string
}

/** The disclosure text and the acknowledgements the backend requires. */
export async function getDisclosures(): Promise<DisclosurePayload | null> {
  try {
    const res = await fetch(`${API}/api/disclosures`)
    if (!res.ok) return null
    return (await res.json()) as DisclosurePayload
  } catch {
    return null
  }
}

/**
 * Record what the consumer actually affirmed.
 *
 * `acks` is passed through exactly as given: the backend rejects the request
 * unless every required id is present and true, and that check is the point.
 */
export async function acknowledgeDisclosures(acks: Record<string, boolean>): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ ok: false, error: 'No active session.' }, 400)
  }
  const res = await fetch(`${API}/api/case/${_sessionId}/acknowledge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ acknowledgements: acks }),
  })
  const data = await readJson(res)
  if (!res.ok) {
    return jsonResponse(
      { ok: false, error: detailMessage(data, 'Could not record your acknowledgements.') },
      res.status,
    )
  }
  return jsonResponse({ ok: true })
}

// ═════════════════════════════════════════════════════════════════════════════
// LETTERS
// ═════════════════════════════════════════════════════════════════════════════

let _letters: GeneratedLetter[] = []

async function fetchLetters(): Promise<GeneratedLetter[]> {
  if (!_sessionId) return []
  const res = await fetch(`${API}/api/case/${_sessionId}/letters`)
  if (!res.ok) throw new Error('Could not load letters')
  const data = await readJson(res)
  _letters = Array.isArray(data.letters) ? (data.letters as GeneratedLetter[]) : []
  return _letters
}

export async function getLetters(): Promise<Response> {
  try {
    const letters = await fetchLetters()
    return jsonResponse({
      ok: true,
      letters: letters.map((l) => ({
        bureau: l.target,
        type_label: 'Dispute Letter',
        variant: 'A',
        title: `Dispute Letter — ${l.target}`,
      })),
    })
  } catch {
    return jsonResponse({ ok: false, error: 'Could not load letters.' }, 502)
  }
}

export async function getLetterById(index: number): Promise<Response> {
  try {
    const letters = _letters.length > 0 ? _letters : await fetchLetters()
    const ltr = letters[index]
    if (!ltr) return jsonResponse({ ok: false, error: 'Letter not found.' }, 404)
    return jsonResponse({
      ok: true,
      letter: {
        bureau: ltr.target,
        type_label: 'Dispute Letter',
        variant: 'A',
        title: `Dispute Letter — ${ltr.target}`,
        body: ltr.text,
        client_name: '',
        client_address: '',
        confirmation: ltr.tracking_number ?? '',
      },
    })
  } catch {
    return jsonResponse({ ok: false, error: 'Could not load letter.' }, 502)
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// PAYMENT — Stripe Checkout (cards; Cash App / Chime users pay there too)
// ═════════════════════════════════════════════════════════════════════════════

async function stripeCheckout(): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ ok: false, error: 'No active session — please complete the intake first.' }, 400)
  }
  const res = await fetch(`${API}/api/case/${_sessionId}/checkout`, { method: 'POST' })
  const data = await readJson(res)
  if (!res.ok) {
    return jsonResponse({ ok: false, error: detailMessage(data, 'Could not start checkout.') }, res.status)
  }
  if (data.checkout_url) {
    return jsonResponse({ ok: true, checkout_url: data.checkout_url })
  }
  // Demo mode / already paid: treat as immediate success (dev_mode keeps the
  // stairway page's existing success branch working unchanged).
  if ((data.demo_mode && data.paid) || data.already_paid) {
    return jsonResponse({ ok: true, dev_mode: true, paid: true })
  }
  return jsonResponse({ ok: false, error: 'Unexpected checkout response.' }, 502)
}

export async function createCheckout(): Promise<Response> {
  return stripeCheckout()
}

// Cash App / Chime: the backend issues a confirmation code; the customer sends
// the money directly with the code in the payment note, and admin verifies +
// releases the letters from /admin.
export async function manualPay(method: 'cashapp' | 'chime'): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ ok: false, error: 'No active session — please complete the intake first.' }, 400)
  }
  const res = await fetch(`${API}/api/case/${_sessionId}/manual-pay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ method }),
  })
  const data = await readJson(res)
  if (!res.ok) {
    return jsonResponse({ ok: false, error: detailMessage(data, 'Could not start payment.') }, res.status)
  }
  if (data.already_paid) {
    return jsonResponse({ ok: true, paid: true })
  }
  return jsonResponse({
    ok: true,
    pending: true,
    confirmation: data.confirmation,
    method: data.method,
    handle: data.handle,
    amount: data.amount,
  })
}

// ═════════════════════════════════════════════════════════════════════════════
// SESSION RESUME / STATUS
// ═════════════════════════════════════════════════════════════════════════════

export async function getCaseStatus(): Promise<CaseStatus | null> {
  if (!_sessionId) return null
  const res = await fetch(`${API}/api/case/${_sessionId}/status`)
  if (!res.ok) return null
  return (await readJson(res)) as unknown as CaseStatus
}

// ═════════════════════════════════════════════════════════════════════════════
// MAIL DISPATCH
// ═════════════════════════════════════════════════════════════════════════════

export async function sendCertified(_dayNumber: number = 0, _mailClass: string = ''): Promise<Response> {
  void _dayNumber; void _mailClass // round/class are fixed server-side (round 1, First Class via Lob)
  if (!_sessionId) {
    return jsonResponse({ ok: false, error: 'No active session — please complete the intake first.' }, 400)
  }
  const res = await fetch(`${API}/api/case/${_sessionId}/send-mail`, { method: 'POST' })
  const data = await readJson(res)
  if (!res.ok) {
    return jsonResponse({ ok: false, error: detailMessage(data, 'Dispatch failed — please try again.') }, res.status)
  }
  const sent = typeof data.sent === 'number' ? data.sent : 0
  const tracking = Array.isArray(data.tracking) ? (data.tracking as MailTracking[]) : []
  if (sent === 0) {
    return jsonResponse({ ok: false, error: String(data.message ?? 'Mailing is not available right now.') }, 502)
  }
  return jsonResponse({
    ok: true,
    sent,
    tracking,
    confirmation_code: tracking[0]?.tracking_number || `AE-${_sessionId.toUpperCase()}`,
    message: data.message,
  })
}

// ═════════════════════════════════════════════════════════════════════════════
// WATCHER — 30/60/90 tracking product is deliberately unscoped in the FastAPI
// backend. Status adapts from case/mail status; subscribe fails gracefully.
// ═════════════════════════════════════════════════════════════════════════════

export async function getWatcherStatus(): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ ok: true, tracking: { dispatched: false, subscribed: false } })
  }
  try {
    const status = await getCaseStatus()
    if (!status) return jsonResponse({ ok: true, tracking: { dispatched: false, subscribed: false } })

    let tracking: MailTracking[] = []
    if (status.paid) {
      const mailRes = await fetch(`${API}/api/case/${_sessionId}/mail-status`)
      if (mailRes.ok) {
        const mailData = await readJson(mailRes)
        tracking = Array.isArray(mailData.tracking) ? (mailData.tracking as MailTracking[]) : []
      }
    }

    const daysSince = status.created_at
      ? Math.max(0, Math.floor((Date.now() - new Date(status.created_at).getTime()) / 86_400_000))
      : 0

    return jsonResponse({
      ok: true,
      tracking: {
        dispatched: status.mail_sent,
        subscribed: false, // Watcher subscriptions are not live yet
        dispatched_at: status.created_at ?? undefined,
        days_since_dispatch: daysSince,
        confirmation: tracking[0]?.tracking_number ?? '',
        letter_count: status.letters_count,
      },
    })
  } catch {
    return jsonResponse({ ok: false, error: 'Could not load tracking status.' }, 502)
  }
}

/**
 * Start checkout for the tracker, which is sold separately from the letters.
 *
 * Returns `{ checkout_url }` to redirect to, or `{ paid: true }` when there is
 * nothing to charge — tracking bundled into the base price, or a dev
 * environment with no Stripe key.
 */
export async function watcherCheckout(): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ error: 'No active session — please complete the intake first.' }, 400)
  }
  const res = await fetch(`${API}/api/case/${_sessionId}/watcher/checkout`, { method: 'POST' })
  const data = await readJson(res)
  if (!res.ok) {
    return jsonResponse({ error: detailMessage(data, 'Could not start checkout for tracking.') }, res.status)
  }
  return jsonResponse(data, res.status)
}

/**
 * Turn the tracker on, after it has been paid for.
 *
 * The backend validates the channel before anything else, so an address it
 * cannot deliver to comes back as `{ ok: false, error, channels }` rather than
 * a subscription that silently never sends. A 402 means checkout has not
 * completed yet.
 */
export async function subscribeWatcher(
  notifyMethod: string,
  notifyHandle: string,
  acceptRetention: boolean = true,
): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ ok: false, error: 'No active session.' }, 400)
  }
  const res = await fetch(`${API}/api/case/${_sessionId}/watcher/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      notify_method: notifyMethod,
      notify_handle: notifyHandle,
      accept_retention: acceptRetention,
    }),
  })
  const data = await readJson(res)
  if (!res.ok) {
    return jsonResponse(
      { ok: false, error: detailMessage(data, 'Could not turn on tracking.'), status: res.status },
      res.status,
    )
  }
  return jsonResponse(data, res.status)
}

/** The generated letters for a milestone round (day 30, 60, 90…). */
export async function getFollowupLetters(day: number): Promise<Response> {
  if (!_sessionId) {
    return jsonResponse({ ok: false, error: 'No active session.' }, 400)
  }
  const res = await fetch(`${API}/api/case/${_sessionId}/watcher/followup/${day}`, {
    method: 'POST',
  })
  const data = await readJson(res)
  if (!res.ok) {
    return jsonResponse(
      { ok: false, error: detailMessage(data, `Could not generate the day-${day} letters.`) },
      res.status,
    )
  }
  return jsonResponse(data, res.status)
}

// ═════════════════════════════════════════════════════════════════════════════
// CREDIT REPORT HOOK — the guide is static content (previously served by the
// retired Flask backend); parsing happens automatically on upload in FastAPI.
// ═════════════════════════════════════════════════════════════════════════════

const CREDIT_REPORT_GUIDE = {
  title: 'Get Your Free Annual Credit Report',
  description: 'Under the Fair Credit Reporting Act, you are entitled to one free credit report per bureau per year.',
  bureaus: ['Equifax', 'TransUnion', 'Experian'],
  steps: [
    {
      number: 1,
      title: 'Visit AnnualCreditReport.com',
      description: 'Go to the official government-authorized website: https://www.annualcreditreport.com',
      action: 'open_link',
      link: 'https://www.annualcreditreport.com',
    },
    {
      number: 2,
      title: 'Select Your State',
      description: 'Choose your state of residence.',
    },
    {
      number: 3,
      title: 'Provide Personal Information',
      description: 'Enter your name, address, Social Security number, and date of birth.',
      warning: 'Only provide this info on the official AnnualCreditReport.com website.',
    },
    {
      number: 4,
      title: 'Choose Bureaus',
      description: 'Select which credit bureaus you want reports from (Equifax, TransUnion, Experian).',
      tip: 'You can get all three reports at once or stagger them throughout the year.',
    },
    {
      number: 5,
      title: 'Verify Your Identity',
      description: 'Complete identity verification (security questions or other methods).',
    },
    {
      number: 6,
      title: 'Download Your Reports',
      description: 'Download reports as PDF. Save them for your records.',
      tip: 'You can also request reports by mail or phone if you prefer.',
    },
    {
      number: 7,
      title: 'Upload to BitmojiGuy',
      description: 'Upload your credit report(s) to the Dojo to identify disputable accounts.',
      action: 'upload_report',
    },
  ],
  phone_number: '1-877-322-8228',
  mail_address: 'Annual Credit Report Request Service, P.O. Box 105281, Atlanta, GA 30348',
  faq: [
    {
      question: 'Is this really free?',
      answer: 'Yes. The federal government requires credit bureaus to provide one free report per year per consumer.',
    },
    {
      question: 'Why should I get my credit report?',
      answer: 'To identify errors, fraud, or negative items that can be disputed under the FCRA.',
    },
    {
      question: 'How long does it take?',
      answer: 'Usually 5-10 minutes online. You can get reports immediately or by mail in 15 days.',
    },
    {
      question: 'What if I find errors?',
      answer: "That's where BitmojiGuy comes in. We help you dispute errors with the credit bureaus.",
    },
  ],
}

const CREDIT_BUREAUS_INFO = {
  Equifax: {
    phone: '1-800-685-1111',
    website: 'https://www.equifax.com',
    dispute_url: 'https://www.equifax.com/personal/credit-report-services/',
  },
  TransUnion: {
    phone: '1-800-916-8800',
    website: 'https://www.transunion.com',
    dispute_url: 'https://www.transunion.com/credit-disputes/dispute-your-credit',
  },
  Experian: {
    phone: '1-888-397-3742',
    website: 'https://www.experian.com',
    dispute_url: 'https://www.experian.com/help/disputes/',
  },
}

export async function getCreditReportGuide(): Promise<Response> {
  return jsonResponse({ ok: true, guide: CREDIT_REPORT_GUIDE })
}

export async function getCreditReportBureaus(): Promise<Response> {
  return jsonResponse({ ok: true, bureaus: CREDIT_BUREAUS_INFO })
}

// Parsing is automatic on upload in the FastAPI backend — resolve immediately
// so the dojo flow proceeds.
export async function parseCreditReport(): Promise<Response> {
  return jsonResponse({ ok: true, status: 'complete', parsed: true })
}

export async function getCreditReportStatus(): Promise<Response> {
  return jsonResponse({ ok: true, status: 'complete' })
}

// ═════════════════════════════════════════════════════════════════════════════
// ADMIN — FastAPI exposes /api/admin/{stats,buckets,templates} guarded by the
// X-Admin-Key header. Flask-era admin workflows have no equivalent and fail
// gracefully.
// ═════════════════════════════════════════════════════════════════════════════

let _adminKey = ''

export function setAdminKey(key: string) { _adminKey = key }

function adminHeaders(): Record<string, string> {
  return { 'X-Admin-Key': _adminKey }
}

export async function adminAuth(key: string): Promise<Response> {
  _adminKey = key
  return fetch(`${API}/api/admin/stats`, { headers: adminHeaders() })
}

export async function adminGetStats(): Promise<Response> {
  return fetch(`${API}/api/admin/stats`, { headers: adminHeaders() })
}

export async function adminGetBuckets(): Promise<Response> {
  return fetch(`${API}/api/admin/buckets`, { headers: adminHeaders() })
}

export async function adminGetTemplates(): Promise<Response> {
  return fetch(`${API}/api/admin/templates`, { headers: adminHeaders() })
}

// Manual-pay release queue: cases waiting on a Cash App / Chime payment.
export async function adminGetPendingPayments(): Promise<Response> {
  return fetch(`${API}/api/admin/pending-payments`, { headers: adminHeaders() })
}

export async function adminReleasePayment(sessionId: string): Promise<Response> {
  return fetch(`${API}/api/admin/release/${sessionId}`, { method: 'POST', headers: adminHeaders() })
}

const ADMIN_NOT_SUPPORTED = 'Not supported by the current backend.'

export async function queueForRelease(): Promise<Response> {
  // Release-queue workflow does not exist in FastAPI: payment (Stripe webhook)
  // triggers mailing directly. Resolve harmlessly.
  return jsonResponse({ ok: true, queued: false, message: ADMIN_NOT_SUPPORTED })
}

export async function adminGetSubmissions(): Promise<Response> {
  return jsonResponse({ ok: false, error: ADMIN_NOT_SUPPORTED }, 501)
}

export async function adminGetPipeline(): Promise<Response> {
  return jsonResponse({ ok: false, error: ADMIN_NOT_SUPPORTED }, 501)
}

export async function adminGetPendingNotifications(): Promise<Response> {
  return jsonResponse({ ok: false, error: ADMIN_NOT_SUPPORTED }, 501)
}

export async function adminApprovePayment(_sessionId: string): Promise<Response> {
  void _sessionId
  return jsonResponse({ ok: false, error: ADMIN_NOT_SUPPORTED }, 501)
}

export async function adminNotifyClient(_sessionId: string, _day: number): Promise<Response> {
  void _sessionId; void _day
  return jsonResponse({ ok: false, error: ADMIN_NOT_SUPPORTED }, 501)
}

export async function adminRunAction(_endpoint: string): Promise<Response> {
  void _endpoint
  return jsonResponse({ ok: false, error: ADMIN_NOT_SUPPORTED }, 501)
}

// ═════════════════════════════════════════════════════════════════════════════
// DOWNLOAD URLS
// ═════════════════════════════════════════════════════════════════════════════

export function getLettersUrl() {
  return `${API}/api/case/${_sessionId}/letters`
}

export function getDownloadPackageUrl() {
  return `${API}/api/case/${_sessionId}/download`
}
