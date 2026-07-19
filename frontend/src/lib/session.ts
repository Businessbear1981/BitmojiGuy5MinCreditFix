// Session persistence: the case session_id lives in localStorage so the
// journey survives page refreshes and the Stripe Checkout redirect.

const KEY = 'cf_session_id';

export function saveSession(sessionId: string) {
  try {
    localStorage.setItem(KEY, sessionId);
  } catch {
    // Storage unavailable (private mode) — the flow still works, it just
    // won't survive a refresh.
  }
}

export function loadSession(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function clearSession() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}
