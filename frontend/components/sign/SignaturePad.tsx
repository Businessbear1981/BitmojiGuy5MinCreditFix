'use client'

import { useEffect, useRef, useState } from 'react'

const ACCENT = '#D94A3B'

interface SignaturePadProps {
  /** Full legal name from intake — pre-fills the confirmation field. */
  defaultName?: string
  /** Called with the PNG data URL and typed name once the consumer signs. */
  onSign: (signature: string, typedName: string) => Promise<void>
  /** Set when a signature is already on file, so the pad shows as done. */
  alreadySigned?: boolean
  signedAt?: string
}

/**
 * Signature capture for the dispute packet.
 *
 * Draws at devicePixelRatio so the exported PNG is crisp when ReportLab
 * scales it into the letter — a 1x canvas looks fine on screen and turns to
 * mush on paper. Pointer events cover mouse, trackpad, stylus and finger in
 * one code path; touch-action is disabled on the canvas so a phone doesn't
 * scroll the page out from under someone mid-signature.
 */
export function SignaturePad({ defaultName = '', onSign, alreadySigned, signedAt }: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const drawing = useRef(false)
  const dirty = useRef(false)
  const last = useRef<{ x: number; y: number } | null>(null)

  const [name, setName] = useState(defaultName)
  const [hasMark, setHasMark] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(Boolean(alreadySigned))

  // Size the backing store to the device pixel ratio, then scale the context
  // so drawing coordinates stay in CSS pixels.
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const resize = () => {
      const ratio = Math.max(window.devicePixelRatio || 1, 2)
      const rect = canvas.getBoundingClientRect()
      // Preserve anything already drawn across a resize.
      const prev = dirty.current ? canvas.toDataURL() : null

      canvas.width = Math.round(rect.width * ratio)
      canvas.height = Math.round(rect.height * ratio)

      const ctx = canvas.getContext('2d')
      if (!ctx) return
      ctx.scale(ratio, ratio)
      ctx.lineWidth = 2.4
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      // Ballpoint blue. The letters instruct 'sign in blue ink', and a
      // blue signature also reads as an original rather than a photocopy
      // to anyone opening the envelope.
      ctx.strokeStyle = '#1B3FA0'

      if (prev) {
        const img = new Image()
        img.onload = () => ctx.drawImage(img, 0, 0, rect.width, rect.height)
        img.src = prev
      }
    }

    resize()
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [])

  function pointFrom(e: React.PointerEvent<HTMLCanvasElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    return { x: e.clientX - rect.left, y: e.clientY - rect.top }
  }

  function start(e: React.PointerEvent<HTMLCanvasElement>) {
    if (done) return
    e.currentTarget.setPointerCapture(e.pointerId)
    drawing.current = true
    last.current = pointFrom(e)
    setError('')
  }

  function move(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawing.current || done) return
    const ctx = canvasRef.current?.getContext('2d')
    if (!ctx || !last.current) return

    const p = pointFrom(e)
    ctx.beginPath()
    ctx.moveTo(last.current.x, last.current.y)
    ctx.lineTo(p.x, p.y)
    ctx.stroke()
    last.current = p

    if (!dirty.current) { dirty.current = true; setHasMark(true) }
  }

  function end(e: React.PointerEvent<HTMLCanvasElement>) {
    drawing.current = false
    last.current = null
    try { e.currentTarget.releasePointerCapture(e.pointerId) } catch { /* already released */ }
  }

  function clear() {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    dirty.current = false
    setHasMark(false)
    setError('')
  }

  async function submit() {
    if (!hasMark) { setError('Please sign in the box above.'); return }
    if (name.trim().length < 2) { setError('Type your full legal name to confirm.'); return }

    const canvas = canvasRef.current
    if (!canvas) return

    setSaving(true); setError('')
    try {
      await onSign(canvas.toDataURL('image/png'), name.trim())
      setDone(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save your signature.')
    } finally {
      setSaving(false)
    }
  }

  if (done) {
    return (
      <div style={{
        padding: '1.25rem 1.4rem',
        border: `1px solid ${ACCENT}55`,
        borderRadius: 6,
        background: `linear-gradient(135deg, ${ACCENT}14, rgba(0,0,0,0.45))`,
      }}>
        <p style={{
          fontFamily: 'var(--font-cinzel), serif', fontSize: 11, letterSpacing: 2,
          textTransform: 'uppercase', color: ACCENT, margin: 0, marginBottom: 6,
        }}>
          ✓ Signed
        </p>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0', margin: 0, lineHeight: 1.6 }}>
          Your signature is on every letter in the packet. Nothing else is needed from you —
          we print and mail them from here.
        </p>
        {signedAt && (
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#B0A99C', margin: '8px 0 0' }}>
            Signed {new Date(signedAt).toLocaleString()}
          </p>
        )}
      </div>
    )
  }

  return (
    <div style={{
      padding: '1.25rem 1.4rem',
      border: `1px solid ${ACCENT}44`,
      borderRadius: 6,
      background: 'rgba(0,0,0,0.45)',
    }}>
      <p style={{
        fontFamily: 'var(--font-cinzel), serif', fontSize: 11, letterSpacing: 2,
        textTransform: 'uppercase', color: ACCENT, margin: 0, marginBottom: 4,
      }}>
        Sign your letters
      </p>
      <p style={{
        fontFamily: 'var(--font-body)', fontSize: 12, color: '#B0A99C',
        margin: '0 0 14px', lineHeight: 1.55,
      }}>
        Sign once — your signature goes on all letters in the packet. Use a finger,
        stylus or mouse.
      </p>

      <div style={{ position: 'relative' }}>
        <canvas
          ref={canvasRef}
          onPointerDown={start}
          onPointerMove={move}
          onPointerUp={end}
          onPointerLeave={end}
          onPointerCancel={end}
          style={{
            width: '100%',
            height: 170,
            display: 'block',
            borderRadius: 4,
            background: '#FBFAF6',
            border: `1px solid ${hasMark ? ACCENT + '88' : 'rgba(138,130,120,0.35)'}`,
            cursor: 'crosshair',
            touchAction: 'none',
          }}
        />
        {/* Signature rule — sits under the stroke, ignores pointer events. */}
        <div style={{
          position: 'absolute', left: 24, right: 24, bottom: 38,
          borderBottom: '1px solid rgba(27,63,160,0.30)', pointerEvents: 'none',
        }} />
        {!hasMark && (
          <span style={{
            position: 'absolute', left: 28, bottom: 44,
            fontFamily: 'var(--font-body)', fontSize: 12, color: 'rgba(27,63,160,0.40)',
            pointerEvents: 'none', userSelect: 'none',
          }}>
            Sign here
          </span>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
        <button
          onClick={clear}
          type="button"
          style={{
            fontFamily: 'var(--font-body)', fontSize: 11, letterSpacing: 1,
            textTransform: 'uppercase', color: '#B0A99C',
            background: 'transparent', border: 'none', cursor: 'pointer', padding: 4,
          }}
        >
          Clear
        </button>
      </div>

      <label style={{
        display: 'block', fontFamily: 'var(--font-body)', fontSize: 11,
        color: '#B0A99C', letterSpacing: 1, textTransform: 'uppercase',
        margin: '10px 0 6px',
      }}>
        Type your full legal name
      </label>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Jordan Reyes"
        autoComplete="name"
        style={{
          width: '100%', padding: '10px 12px', borderRadius: 4,
          background: 'rgba(0,0,0,0.5)', color: '#F0EBE0',
          border: '1px solid rgba(138,130,120,0.35)',
          fontFamily: 'var(--font-body)', fontSize: 14,
        }}
      />

      <p style={{
        fontFamily: 'var(--font-body)', fontSize: 10.5, color: '#8A8278',
        lineHeight: 1.55, margin: '12px 0 0',
      }}>
        By signing you confirm the disputes are accurate to the best of your knowledge and
        authorise these letters to be sent in your name. This is an electronic signature under
        the E-SIGN Act (15 U.S.C. § 7001).
      </p>

      {error && (
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#FF6B6B', margin: '10px 0 0' }}>
          {error}
        </p>
      )}

      <button
        onClick={submit}
        disabled={saving}
        style={{
          width: '100%', marginTop: 14,
          fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 3,
          textTransform: 'uppercase', color: '#12100C',
          background: saving
            ? 'rgba(120,120,120,0.4)'
            : `linear-gradient(135deg, ${ACCENT}, #A8321F)`,
          padding: '13px 0', borderRadius: 4, border: 'none',
          cursor: saving ? 'wait' : 'pointer',
          boxShadow: saving ? 'none' : `0 4px 20px ${ACCENT}44`,
        }}
      >
        {saving ? 'Saving…' : 'Sign & authorise'}
      </button>
    </div>
  )
}
