// BitmojiGuy 5-Min Credit Fix — Type Definitions
// AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital

export interface DisputeItem {
  type: string;
  label: string;
  text: string;
}

export interface ParsedDisputes {
  [key: string]: {
    label: string;
    items: string[];
  };
}

export interface Letter {
  bureau: string;
  bureau_address: string;
  type: string;
  type_label: string;
  variant: string;
  title: string;
  body: string;
}

export interface StartResponse {
  ok: boolean;
  session_id: string;
  name: string;
}

export interface UploadResponse {
  ok: boolean;
  files_received: number;
  parsed_disputes: ParsedDisputes;
  dispute_items: DisputeItem[];
}

export interface ReviewResponse {
  ok: boolean;
  confirmation: string;
  dispute_types: string[];
  dispute_order: string[];
  letter_count: number;
  items: DisputeItem[];
}

export interface CheckoutResponse {
  ok: boolean;
  dev_mode?: boolean;
  message?: string;
  checkout_url?: string;
  session_id?: string;
}

export interface LettersResponse {
  ok: boolean;
  confirmation: string;
  name: string;
  letters: Letter[];
  dispute_types: string[];
}

export interface StatusResponse {
  found: boolean;
  status?: string;
  dispute_count?: number;
  created_at?: string;
}

export const GILMORE_ORDER = [
  'wrong_addresses',
  'unknown_accounts',
  'collections',
  'aged_debt',
  'late_payments',
  'mov_demand',
] as const;

export const GILMORE_PHASES: Record<string, string> = {
  wrong_addresses: 'Phase 1: Personal Info',
  unknown_accounts: 'Phase 2: Inquiries',
  collections: 'Phase 3: Collections',
  aged_debt: 'Phase 4: Charge-Offs',
  late_payments: 'Phase 5: Late Payments',
  mov_demand: 'Follow-Up: MOV',
};

export const DISPUTE_LABELS: Record<string, string> = {
  collections: 'Collection',
  late_payments: 'Late Payment',
  wrong_addresses: 'Wrong Address',
  unknown_accounts: 'Unknown Account',
  aged_debt: 'Aged Debt',
  mov_demand: 'MOV Demand',
};

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
