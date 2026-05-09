'use client'

import { useState, useRef } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { SceneLayout } from '@/components/scene/SceneLayout'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { sendCertified, uploadSupportingDoc } from '@/lib/api'

const ACCENT = '#D94A3B'

export default function GatePage() {
  const { navigateTo } = useShojiNav()
  const [postage, setPostage] = useState<'first' | 'certified'>('certified')
  const [sending, setSending] = useState(false)
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')

  // Supporting doc uploads
  const [idFile, setIdFile] = useState<File | null>(null)
  const [addressFile, setAddressFile] = useState<File | null>(null)
  const [idUploaded, setIdUploaded] = useState(false)
  const [addressUploaded, setAddressUploaded] = useState(false)
  const [uploading, setUploading] = useState(false)
  const idInputRef = useRef<HTMLInputElement>(null)
  const addrInputRef = useRef<HTMLInputElement>(null)

  async function handleDocUpload(file: File, docType: 'id_document' | 'address_proof') {
    setError('')
    setUploading(true)
    try {
      const res = await uploadSupportingDoc(file, docType)
      const data = await res.json()
      if (data.ok) {
        if (docType === 'id_document') setIdUploaded(true)
        else setAddressUploaded(true)
      } else {
        setError(data.error || 'Upload failed')
      }
    } catch {
      setError('Could not upload document. Try again.')
    } finally {
      setUploading(false)
    }
  }

  async function handleDispatch() {
    setError('')
    if (!idUploaded || !addressUploaded) {
      setError('Upload both your government ID and proof of address before dispatch.')
      return
    }
    setSending(true)
    try {
      const mailClass = postage === 'certified' ? 'Certified Mail' : 'First Class'
      const res = await sendCertified(mailClass)
      const data = await res.json()
      if (data.confirmation_code || data.sent > 0) {
        setConfirmation(data.confirmation_code || '')
      } else {
        setError(data.error || 'No letters dispatched')
      }
    } catch {
      setError('Could not connect to server. Try again.')
    } finally {
      setSending(false)
    }
  }

  return (
    <SceneLayout preset="nirvana">
      <TopNav currentStep={6} />

      <div style={{
        padding: '8px 24px', textAlign: 'center',
        background: 'rgba(217,74,59,0.05)', borderBottom: '1px solid rgba(217,74,59,0.15)',
        fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
        color: ACCENT, letterSpacing: 2,
        textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 12px ${ACCENT}88, 0 0 24px ${ACCENT}44`,
      }}>
        &ldquo;The dragon&apos;s gate opens once. Send the mail. The sky records your dispatch.&rdquo;
      </div>

      <div style={{ flex: 1, display: 'flex' }}>
        <WizardSidebar
          step={6}
          mascotSpeech="Stamp it. Ship it. The bureaus must answer under FCRA 611."
        />

        <div style={{
          flex: 1, padding: '2rem',
          background: 'rgba(14,6,6,0.25)',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
        }}>
          <div style={{ width: '100%', maxWidth: 560 }}>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT,
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4,
            }}>
              Step 6 of 7 &middot; 門 &middot; Dragon&apos;s Gate
            </p>
            <h2 style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: '1.6rem', color: '#F0EBE0', letterSpacing: 2,
              marginTop: 0, marginBottom: 6,
              textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 24px ${ACCENT}55`,
            }}>
              Dispatch the Letters
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278',
              fontStyle: 'italic', marginBottom: 24,
            }}>
              Your certified confirmation number is your receipt of legal service
            </p>

            {/* Postage picker */}
            <div style={{
              border: `1px solid ${ACCENT}33`,
              borderRadius: 6, padding: '1rem',
              background: 'rgba(6,3,3,0.3)',
              marginBottom: 20,
            }}>
              <p style={{
                fontFamily: 'var(--font-cinzel), serif', fontSize: '0.72rem',
                color: ACCENT, letterSpacing: 1.5, marginBottom: 12,
                textTransform: 'uppercase',
              }}>
                Postage Class
              </p>

              <label style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                borderRadius: 4, cursor: 'pointer', marginBottom: 6,
                border: postage === 'first' ? `1px solid ${ACCENT}66` : '1px solid rgba(138,130,120,0.15)',
                background: postage === 'first' ? `${ACCENT}11` : 'transparent',
                transition: 'all 0.2s',
              }}>
                <input
                  type="radio" name="postage" value="first"
                  checked={postage === 'first'}
                  onChange={() => setPostage('first')}
                  style={{ accentColor: ACCENT }}
                />
                <div>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0' }}>
                    First Class with Tracking
                  </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT, marginLeft: 8 }}>
                    $3/letter
                  </span>
                </div>
              </label>

              <label style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                borderRadius: 4, cursor: 'pointer',
                border: postage === 'certified' ? `1px solid ${ACCENT}66` : '1px solid rgba(138,130,120,0.15)',
                background: postage === 'certified' ? `${ACCENT}11` : 'transparent',
                transition: 'all 0.2s',
              }}>
                <input
                  type="radio" name="postage" value="certified"
                  checked={postage === 'certified'}
                  onChange={() => setPostage('certified')}
                  style={{ accentColor: ACCENT }}
                />
                <div>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0' }}>
                    Certified Mail &middot; Return Receipt
                  </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT, marginLeft: 8 }}>
                    $8/letter
                  </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 10, color: '#8A8278', display: 'block', marginTop: 2 }}>
                    Recommended &middot; proof of delivery for FCRA disputes
                  </span>
                </div>
              </label>
            </div>

            {/* Supporting docs — the two plugs on the power strip */}
            <div style={{
              border: `1px solid ${ACCENT}33`,
              borderRadius: 6, padding: '1rem',
              background: 'rgba(6,3,3,0.3)',
              marginBottom: 20,
            }}>
              <p style={{
                fontFamily: 'var(--font-cinzel), serif', fontSize: '0.72rem',
                color: ACCENT, letterSpacing: 1.5, marginBottom: 12,
                textTransform: 'uppercase',
              }}>
                Required Documents
              </p>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
                marginBottom: 14, lineHeight: 1.5,
              }}>
                Each bureau envelope will include your dispute letter + copies of these documents.
              </p>

              {/* Plug 1 — Government ID */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 12px', borderRadius: 4, marginBottom: 8,
                border: idUploaded ? `1px solid #4CAF5066` : `1px solid rgba(138,130,120,0.15)`,
                background: idUploaded ? 'rgba(76,175,80,0.06)' : 'transparent',
              }}>
                <div style={{ flex: 1 }}>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0' }}>
                    Government-Issued ID
                  </span>
                  <span style={{
                    fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
                    display: 'block', marginTop: 2,
                  }}>
                    {idUploaded
                      ? `${idFile?.name ?? 'Uploaded'}`
                      : "Driver's license, passport, or state ID"}
                  </span>
                </div>
                <input
                  ref={idInputRef}
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  style={{ display: 'none' }}
                  onChange={async (e) => {
                    const f = e.target.files?.[0]
                    if (f) { setIdFile(f); await handleDocUpload(f, 'id_document') }
                  }}
                />
                <button
                  onClick={() => idInputRef.current?.click()}
                  disabled={uploading}
                  style={{
                    fontFamily: 'var(--font-heading)', fontSize: 11, letterSpacing: 1.5,
                    textTransform: 'uppercase',
                    color: idUploaded ? '#4CAF50' : ACCENT,
                    background: 'transparent',
                    padding: '6px 14px', borderRadius: 4,
                    border: `1px solid ${idUploaded ? '#4CAF5066' : ACCENT + '44'}`,
                    cursor: uploading ? 'wait' : 'pointer',
                  }}
                >
                  {idUploaded ? 'Replace' : 'Upload'}
                </button>
              </div>

              {/* Plug 2 — Proof of Address */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 12px', borderRadius: 4,
                border: addressUploaded ? `1px solid #4CAF5066` : `1px solid rgba(138,130,120,0.15)`,
                background: addressUploaded ? 'rgba(76,175,80,0.06)' : 'transparent',
              }}>
                <div style={{ flex: 1 }}>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#F0EBE0' }}>
                    Proof of Address
                  </span>
                  <span style={{
                    fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
                    display: 'block', marginTop: 2,
                  }}>
                    {addressUploaded
                      ? `${addressFile?.name ?? 'Uploaded'}`
                      : 'Utility bill, bank statement, or lease (recent)'}
                  </span>
                </div>
                <input
                  ref={addrInputRef}
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  style={{ display: 'none' }}
                  onChange={async (e) => {
                    const f = e.target.files?.[0]
                    if (f) { setAddressFile(f); await handleDocUpload(f, 'address_proof') }
                  }}
                />
                <button
                  onClick={() => addrInputRef.current?.click()}
                  disabled={uploading}
                  style={{
                    fontFamily: 'var(--font-heading)', fontSize: 11, letterSpacing: 1.5,
                    textTransform: 'uppercase',
                    color: addressUploaded ? '#4CAF50' : ACCENT,
                    background: 'transparent',
                    padding: '6px 14px', borderRadius: 4,
                    border: `1px solid ${addressUploaded ? '#4CAF5066' : ACCENT + '44'}`,
                    cursor: uploading ? 'wait' : 'pointer',
                  }}
                >
                  {addressUploaded ? 'Replace' : 'Upload'}
                </button>
              </div>
            </div>

            {error && (
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#FF4444', marginBottom: 12 }}>
                {error}
              </p>
            )}

            {confirmation ? (
              <div style={{
                padding: '1.5rem',
                border: `1px solid ${ACCENT}`,
                borderRadius: 6,
                background: `linear-gradient(135deg, ${ACCENT}22, rgba(0,0,0,0.6))`,
                marginBottom: 20,
                textAlign: 'center',
                boxShadow: `0 0 30px ${ACCENT}44`,
              }}>
                <p style={{
                  fontFamily: 'var(--font-cinzel), serif', fontSize: '0.7rem',
                  color: ACCENT, letterSpacing: 2, textTransform: 'uppercase',
                  marginBottom: 8,
                }}>
                  Confirmation Number
                </p>
                <p style={{
                  fontFamily: 'var(--font-cinzel-decorative), serif',
                  fontSize: '1.6rem', color: '#F0EBE0', letterSpacing: 3,
                  margin: 0,
                }}>
                  {confirmation}
                </p>
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
                  letterSpacing: 1, marginTop: 10,
                }}>
                  Dispatched via {postage === 'certified' ? 'Certified Mail' : 'First Class'} &middot; Save this number
                </p>
              </div>
            ) : (
              <button
                onClick={handleDispatch}
                disabled={sending}
                style={{
                  width: '100%',
                  fontFamily: 'var(--font-heading)', fontSize: 15, letterSpacing: 3,
                  textTransform: 'uppercase', color: '#050403',
                  background: `linear-gradient(135deg, ${ACCENT}, #7A1F1B)`,
                  padding: '14px 0', borderRadius: 4, border: 'none',
                  cursor: sending ? 'wait' : 'pointer',
                  boxShadow: `0 4px 24px ${ACCENT}55`,
                  opacity: sending ? 0.7 : 1,
                  marginBottom: 20,
                }}
              >
                {sending ? 'Dispatching...' : '✉ Dispatch All Letters Through the Gate'}
              </button>
            )}

            <div style={{ display: 'flex', gap: 12, justifyContent: 'space-between' }}>
              <button
                onClick={() => navigateTo('/stairway')}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: '#8A8278', background: 'transparent',
                  padding: '10px 24px', borderRadius: 4,
                  border: '1px solid rgba(138,130,120,0.3)', cursor: 'pointer',
                }}
              >
                &larr; Back
              </button>
              {confirmation && (
                <button
                  onClick={() => navigateTo('/watcher')}
                  style={{
                    fontFamily: 'var(--font-heading)', fontSize: 14, letterSpacing: 3,
                    textTransform: 'uppercase', color: '#050403',
                    background: 'linear-gradient(135deg, #8CB4FF, #3A5FB3)',
                    padding: '12px 40px', borderRadius: 4, border: 'none',
                    cursor: 'pointer',
                    boxShadow: '0 4px 20px rgba(140,180,255,0.3)',
                  }}
                >
                  Continue to The Watcher &rarr;
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </SceneLayout>
  )
}
