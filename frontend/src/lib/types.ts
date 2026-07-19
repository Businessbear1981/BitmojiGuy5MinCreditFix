// AE 5-Min Credit Fix — Type definitions for the FastAPI backend
// AE Labs — Sean Gilmore / Arden Edge Capital

export const PRICE_DISPLAY = '$24.99';

/** A disputable item detected by the report scanner (backend suggestion). */
export interface Suggestion {
  bucket: string;
  type: 'bureau' | 'creditor';
  target: string;
  account: string;
  amount: number | null;
  opened: string | null;
  reason: string;
  confidence: 'high' | 'medium' | 'low';
}

/** A dispute item as confirmed by the customer (backend request shape). */
export interface DisputeItemInput {
  type: 'bureau' | 'creditor';
  target: string;
  account: string;
  amount?: number | null;
  opened?: string | null;
  reason: string;
}

export interface GeneratedLetter {
  id: string;
  target: string;
  text: string;
  mail_status?: string;
  tracking_number?: string;
}

export interface CreateCaseResponse {
  session_id: string;
  status: string;
  region: string;
  queue_position: number;
}

export interface UploadResponse {
  filename: string;
  attachments: string[];
  suggestions: Suggestion[];
}

export interface LettersResponse {
  letters: GeneratedLetter[];
  cover_sheet: string;
  total: number;
}

export interface CheckoutResponse {
  checkout_url?: string;
  demo_mode?: boolean;
  paid?: boolean;
  already_paid?: boolean;
  session_id?: string;
}

export interface CaseStatus {
  session_id: string;
  name: string;
  email: string;
  docs_complete: boolean;
  items_count: number;
  letters_count: number;
  paid: boolean;
  email_sent: boolean;
  mail_sent: boolean;
  created_at: string | null;
}

export interface MailStatus {
  status: 'sent' | 'processing';
  tracking: Array<{
    target: string;
    tracking_number: string;
    expected_delivery: string;
    status: string;
  }>;
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
};

/** Beta launch regions enforced by the backend fishbowl. */
export const BETA_STATES = ['TX', 'CA', 'WA'] as const;

export const US_STATES = [
  { value: 'AL', label: 'Alabama' }, { value: 'AK', label: 'Alaska' },
  { value: 'AZ', label: 'Arizona' }, { value: 'AR', label: 'Arkansas' },
  { value: 'CA', label: 'California' }, { value: 'CO', label: 'Colorado' },
  { value: 'CT', label: 'Connecticut' }, { value: 'DE', label: 'Delaware' },
  { value: 'DC', label: 'District of Columbia' },
  { value: 'FL', label: 'Florida' }, { value: 'GA', label: 'Georgia' },
  { value: 'HI', label: 'Hawaii' }, { value: 'ID', label: 'Idaho' },
  { value: 'IL', label: 'Illinois' }, { value: 'IN', label: 'Indiana' },
  { value: 'IA', label: 'Iowa' }, { value: 'KS', label: 'Kansas' },
  { value: 'KY', label: 'Kentucky' }, { value: 'LA', label: 'Louisiana' },
  { value: 'ME', label: 'Maine' }, { value: 'MD', label: 'Maryland' },
  { value: 'MA', label: 'Massachusetts' }, { value: 'MI', label: 'Michigan' },
  { value: 'MN', label: 'Minnesota' }, { value: 'MS', label: 'Mississippi' },
  { value: 'MO', label: 'Missouri' }, { value: 'MT', label: 'Montana' },
  { value: 'NE', label: 'Nebraska' }, { value: 'NV', label: 'Nevada' },
  { value: 'NH', label: 'New Hampshire' }, { value: 'NJ', label: 'New Jersey' },
  { value: 'NM', label: 'New Mexico' }, { value: 'NY', label: 'New York' },
  { value: 'NC', label: 'North Carolina' }, { value: 'ND', label: 'North Dakota' },
  { value: 'OH', label: 'Ohio' }, { value: 'OK', label: 'Oklahoma' },
  { value: 'OR', label: 'Oregon' }, { value: 'PA', label: 'Pennsylvania' },
  { value: 'RI', label: 'Rhode Island' }, { value: 'SC', label: 'South Carolina' },
  { value: 'SD', label: 'South Dakota' }, { value: 'TN', label: 'Tennessee' },
  { value: 'TX', label: 'Texas' }, { value: 'UT', label: 'Utah' },
  { value: 'VT', label: 'Vermont' }, { value: 'VA', label: 'Virginia' },
  { value: 'WA', label: 'Washington' }, { value: 'WV', label: 'West Virginia' },
  { value: 'WI', label: 'Wisconsin' }, { value: 'WY', label: 'Wyoming' },
] as const;
