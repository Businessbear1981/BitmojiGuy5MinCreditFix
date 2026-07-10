// BitmojiGuy 5-Min Credit Fix — API Client
// Talks to Flask backend at /api/*

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...opts,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data as T;
}

export async function startSession(name: string, email: string, phone: string, state: string) {
  return request<{ ok: boolean; session_id: string; name: string }>('/api/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, phone, state }),
  });
}

export async function uploadFiles(files: File[]) {
  const fd = new FormData();
  files.forEach((f, i) => fd.append(`file${i}`, f));
  return request<{
    ok: boolean;
    files_received: number;
    parsed_disputes: Record<string, { label: string; items: string[] }>;
    dispute_items: Array<{ type: string; label: string; text: string }>;
  }>('/api/upload', { method: 'POST', body: fd });
}

export async function reviewDisputes(
  items: Array<{ type: string; label: string; text: string }>,
  customItems: Array<{ type: string; label: string; text: string }>
) {
  return request<{
    ok: boolean;
    confirmation: string;
    dispute_types: string[];
    dispute_order: string[];
    letter_count: number;
    items: Array<{ type: string; label: string; text: string }>;
  }>('/api/review', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items, custom_items: customItems }),
  });
}

export async function createCheckout() {
  return request<{
    ok: boolean;
    dev_mode?: boolean;
    message?: string;
    checkout_url?: string;
  }>('/api/create-checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  });
}

export async function manualPay(method: string) {
  return request<{ ok: boolean; confirmation?: string }>('/api/manual-pay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ method }),
  });
}

export async function getLetters() {
  return request<{
    ok: boolean;
    confirmation: string;
    name: string;
    letters: Array<{
      bureau: string;
      bureau_address: string;
      type: string;
      type_label: string;
      variant: string;
      title: string;
      body: string;
    }>;
    dispute_types: string[];
  }>('/api/letters');
}

export async function checkStatus(confirmation: string) {
  return request<{
    found: boolean;
    status?: string;
    dispute_count?: number;
    created_at?: string;
  }>(`/api/status/${encodeURIComponent(confirmation)}`);
}

export async function getFollowupLetters(day: number) {
  return request<{
    ok: boolean;
    letters: Array<{
      bureau: string;
      bureau_address: string;
      type: string;
      type_label: string;
      variant: string;
      title: string;
      body: string;
    }>;
    day: number;
  }>(`/api/followup-letters/${day}`);
}
