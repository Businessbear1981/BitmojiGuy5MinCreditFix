// AE 5-Min Credit Fix — Typed client for the FastAPI backend (/api/case/*)

import type {
  CaseStatus,
  CheckoutResponse,
  CreateCaseResponse,
  DisputeItemInput,
  GeneratedLetter,
  LettersResponse,
  MailStatus,
  UploadResponse,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, opts);
  } catch {
    throw new ApiError(0, 'Cannot reach the server — check your connection and try again.');
  }
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    // non-JSON body (unexpected) — fall through to generic error
  }
  if (!res.ok) {
    const detail =
      data && typeof data === 'object' && 'detail' in data
        ? (data as { detail: unknown }).detail
        : null;
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail) && detail[0]?.msg
        ? String(detail[0].msg)
        : 'Request failed — please try again.';
    throw new ApiError(res.status, message);
  }
  return data as T;
}

function json(body: unknown): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
}

// ── Terms / consent ──────────────────────────────────────────────────────────

export async function acceptTerms(): Promise<{ terms_token: string; accepted_at: string }> {
  return request('/api/terms/accept', { method: 'POST' });
}

// ── Case lifecycle ───────────────────────────────────────────────────────────

export interface CreateCaseInput {
  name: string;
  address: string;
  dob: string;
  ssn_last4: string;
  phone: string;
  email: string;
}

export async function createCase(input: CreateCaseInput, termsToken: string): Promise<CreateCaseResponse> {
  return request('/api/case', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Terms-Token': termsToken },
    body: JSON.stringify(input),
  });
}

export async function uploadDocument(sessionId: string, file: File): Promise<UploadResponse> {
  const fd = new FormData();
  fd.append('file', file);
  return request(`/api/case/${sessionId}/upload`, { method: 'POST', body: fd });
}

export async function confirmDisputes(sessionId: string, items: DisputeItemInput[]): Promise<{ items_count: number }> {
  return request(`/api/case/${sessionId}/disputes`, json({ items }));
}

export async function generateLetters(sessionId: string): Promise<LettersResponse> {
  return request(`/api/case/${sessionId}/letters`, { method: 'POST' });
}

export async function getLetters(sessionId: string): Promise<{ letters: GeneratedLetter[] }> {
  return request(`/api/case/${sessionId}/letters`);
}

export async function createCheckout(sessionId: string): Promise<CheckoutResponse> {
  return request(`/api/case/${sessionId}/checkout`, { method: 'POST' });
}

export async function getCaseStatus(sessionId: string): Promise<CaseStatus> {
  return request(`/api/case/${sessionId}/status`);
}

export async function getMailStatus(sessionId: string): Promise<MailStatus> {
  return request(`/api/case/${sessionId}/mail-status`);
}

export function downloadUrl(sessionId: string): string {
  return `${API_BASE}/api/case/${sessionId}/download`;
}
