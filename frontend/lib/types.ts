// AE 5-Min Credit Fix — Type definitions for the FastAPI backend
// AE Labs — Sean Gilmore / Arden Edge Capital

export const PRICE_DISPLAY = '$24.99'

/** A disputable item detected by the report scanner (backend suggestion). */
export interface Suggestion {
  bucket: string
  type: 'bureau' | 'creditor'
  target: string
  account: string
  amount: number | null
  opened: string | null
  reason: string
  confidence: 'high' | 'medium' | 'low'
}

/** A dispute item as confirmed by the customer (backend request shape). */
export interface DisputeItemInput {
  type: 'bureau' | 'creditor'
  target: string
  account: string
  amount?: number | null
  opened?: string | null
  reason: string
}

export interface GeneratedLetter {
  id: string
  target: string
  text: string
  mail_status?: string
  tracking_number?: string
}

export interface CreateCaseResponse {
  session_id: string
  status: string
  region: string
  queue_position: number
}

export interface UploadResponse {
  filename: string
  attachments: string[]
  suggestions: Suggestion[]
}

export interface CheckoutResponse {
  checkout_url?: string
  demo_mode?: boolean
  paid?: boolean
  already_paid?: boolean
  session_id?: string
}

export interface CaseStatus {
  session_id: string
  name: string
  email: string
  docs_complete: boolean
  items_count: number
  letters_count: number
  paid: boolean
  email_sent: boolean
  mail_sent: boolean
  created_at: string | null
  manual_pay_pending?: boolean
  manual_pay_method?: 'cashapp' | 'chime' | null
  manual_pay_code?: string | null
}

/** Cash App / Chime handles shown on the payment page. Must match the
 *  backend's CASHAPP_CASHTAG / CHIME_TAG config (source of truth for the
 *  pending-payment instructions is the manual-pay API response). */
export const MANUAL_PAY_HANDLES = {
  cashapp: { label: 'Cash App', handle: '$5mincreditfix' },
  chime: { label: 'Chime', handle: '$AELabsPay' },
} as const

export interface ManualPayPending {
  confirmation: string
  method: 'cashapp' | 'chime'
  handle: string
  amount: string
}

export interface MailTracking {
  target: string
  tracking_number: string
  expected_delivery: string
  status: string
}

export interface MailStatus {
  status: 'sent' | 'processing'
  tracking: MailTracking[]
}

export const BUCKET_LABELS: Record<string, string> = {
  collection: 'Collection',
  late_payment: 'Late Payment',
  charge_off: 'Charge-Off',
  identity_error: 'Not My Account',
  inquiry: 'Hard Inquiry',
  medical_debt: 'Medical Debt',
  creditor_direct: 'Creditor Direct',
  obsolete: 'Obsolete (>7yr)',
}
