const FLASK = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'

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
  return fetch(`${FLASK}/api/upload`, { method: 'POST', credentials: 'include', body: fd })
}

export async function getLetters() {
  return fetch(`${FLASK}/api/letters`, { credentials: 'include' })
}

export async function createCheckout() {
  return fetch(`${FLASK}/api/create-checkout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: '{}',
  })
}

export async function reviewDisputes(items: object[], customItems: object[]) {
  return fetch(`${FLASK}/api/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ items, custom_items: customItems }),
  })
}

export async function manualPay(method: string) {
  return fetch(`${FLASK}/api/manual-pay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ method }),
  })
}
