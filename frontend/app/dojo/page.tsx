'use client'

import { useState, useRef, useEffect } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { useWizardStore } from '@/store/wizardStore'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { ArmorWarrior } from '@/components/warrior/ArmorWarrior'
import { CreditReportGuide } from '@/components/dojo/CreditReportGuide'
import { uploadDocument } from '@/lib/api'

const ACCENT = '#C9A84C'

type DocType = 'id' | 'address' | 'report'

interface SlotState {
  armored: boolean
  filename: string
  sizeKb: number
  uploading: boolean
  error: string
}

interface SlotConfig {
  key: DocType
  kanji: string
  armor: string
  title: string
  hint: string
}

const SLOTS: SlotConfig[] = [
  { key: 'id',      kanji: '面', armor: 'Helm',      title: 'Photo ID',         hint: 'Upload a picture of your ID · Driver license or state ID · Required for dispute mailing' },
  { key: 'address', kanji: '鎧', armor: 'Breastplate', title: 'Proof of Residence', hint: 'Utility bill · Bank statement · Lease · Required for dispute mailing' },
  { key: 'report',  kanji: '剣', armor: 'Sword',     title: 'Credit Report',    hint: 'Annualcreditreport.com PDF · CSV · TXT · All documents mailed with your dispute package' },
]

export default function DojoPage() {
  const { navigateTo } = useShojiNav()
  const { uploads, setUpload } = useWizardStore()
  const [slots, setSlots] = useState<Record<DocType, SlotState>>({
    id:      { armored: uploads.idUploaded,      filename: '', sizeKb: 0, uploading: false, error: '' },
    address: { armored: uploads.addressUploaded, filename: '', sizeKb: 0, uploading: false, error: '' },
    report:  { armored: uploads.reportUploaded,  filename: '', sizeKb: 0, uploading: false, error: '' },
  })

  const allArmored = slots.id.armored && slots.address.armored && slots.report.armored

  // Unsheathe the sword once all 3 pieces are forged
  useEffect(() => {
    if (allArmored && !uploads.swordUnsheathed) {
      setUpload('swordUnsheathed', true)
    }
  }, [allArmored, uploads.swordUnsheathed, setUpload])

  async function handleFile(key: DocType, file: File) {
    setSlots((s) => ({ ...s, [key]: { ...s[key], uploading: true, error: '', filename: file.name, sizeKb: Math.round(file.size / 1024) } }))
    try {
      const res = await uploadDocument(file, key)
      const ok = res.ok
      if (!ok) throw new Error(`Upload failed (${res.status})`)
      setSlots((s) => ({ ...s, [key]: { ...s[key], uploading: false, armored: true, error: '' } }))
      setUpload(`${key}Uploaded` as 'idUploaded' | 'addressUploaded' | 'reportUploaded', true)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      setSlots((s) => ({ ...s, [key]: { ...s[key], uploading: false, armored: false, error: `Error: ${msg}` } }))
    }
  }

  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="https://d2xsxph8kpxj0f.cloudfront.net/310519663623353486/TFHGKZ8eZeQPrrYUXjWpCv/dojo_armament_chamber-LwbeaVELoEunDtbgDdwxbA.webp"
        alt=""
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          objectFit: 'cover',
          zIndex: 0,
        }}
      />
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 1 }} />
      <div style={{ position: 'relative', zIndex: 2, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopNav currentStep={2} />

      <div style={{
        padding: '8px 24px', textAlign: 'center',
        background: `${ACCENT}0A`, borderBottom: `1px solid ${ACCENT}22`,
        fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
        color: ACCENT, letterSpacing: 2,
      }}>
        &ldquo;Three pieces of armor. Each one earned by an upload. The warrior must be complete.&rdquo;
      </div>

      <div style={{ flex: 1, display: 'flex' }}>
        <WizardSidebar
          step={2}
          mascotSpeech="Three uploads. Three pieces of armor. Helm, breastplate, sword. Then we march."
        />

        <div style={{
          flex: 1, padding: '2rem',
          background: 'rgba(14,10,4,0.25)',
        }}>
          <div style={{ maxWidth: 780, margin: '0 auto' }}>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 12, color: ACCENT,
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4,
            }}>
              Step 2 of 7 &middot; 武 &middot; The Dojo
            </p>
            <h2 style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: '1.6rem', color: '#F0EBE0', letterSpacing: 2,
              marginTop: 0, marginBottom: 6,
              textShadow: `0 0 24px ${ACCENT}55`,
            }}>
              Suit Up — Upload Your Documents
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278',
              fontStyle: 'italic', marginBottom: 20,
            }}>
              Each document is a piece of armor. All three must be forged.
            </p>

            {/* Armor progress strip */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 16px',
              background: `${ACCENT}11`, borderLeft: `3px solid ${ACCENT}`,
              borderRadius: 4, marginBottom: 20,
            }}>
              <span style={{
                fontFamily: 'var(--font-cinzel), serif', fontSize: 13,
                color: ACCENT, letterSpacing: 2, textTransform: 'uppercase',
              }}>
                Armor: {[slots.id.armored, slots.address.armored, slots.report.armored].filter(Boolean).length} of 3 forged
              </span>
              <span style={{
                fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
              }}>
                {allArmored ? '⚔ Sword unsheathed' : 'Continue locked'}
              </span>
            </div>

            {/* Warrior figure + upload slots side-by-side */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '220px 1fr',
              gap: 28,
              alignItems: 'start',
              marginBottom: 24,
            }}>
              {/* Samurai figure — armors up as uploads complete */}
              <div style={{
                position: 'sticky',
                top: 100,
                display: 'flex',
                justifyContent: 'center',
                paddingTop: 8,
              }}>
                <ArmorWarrior
                  idUploaded={slots.id.armored}
                  addressUploaded={slots.address.armored}
                  reportUploaded={slots.report.armored}
                  swordUnsheathed={allArmored}
                />
              </div>

              {/* Upload slots */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {SLOTS.map((cfg) => (
                  <UploadSlot
                    key={cfg.key}
                    cfg={cfg}
                    state={slots[cfg.key]}
                    onFile={(f) => handleFile(cfg.key, f)}
                  />
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'space-between' }}>
              <button
                onClick={() => navigateTo('/map')}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                  textTransform: 'uppercase', color: '#8A8278', background: 'transparent',
                  padding: '10px 24px', borderRadius: 4,
                  border: '1px solid rgba(138,130,120,0.3)', cursor: 'pointer',
                }}
              >
                &larr; Back
              </button>
              <button
                onClick={() => navigateTo('/koi-pond')}
                disabled={!allArmored}
                style={{
                  fontFamily: 'var(--font-heading)', fontSize: 14, letterSpacing: 3,
                  textTransform: 'uppercase', color: '#050403',
                  background: allArmored
                    ? `linear-gradient(135deg, ${ACCENT}, #8B6914)`
                    : 'rgba(100,100,100,0.3)',
                  padding: '12px 40px', borderRadius: 4, border: 'none',
                  cursor: allArmored ? 'pointer' : 'not-allowed',
                  boxShadow: allArmored ? `0 4px 20px ${ACCENT}55` : 'none',
                  opacity: allArmored ? 1 : 0.5,
                }}
              >
                {allArmored ? 'March to the Koi Pond →' : 'Forge all 3 to continue'}
              </button>
            </div>

            {/* Credit Report Guide */}
            <div style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: `1px solid ${ACCENT}33` }}>
              <div style={{ textAlign: 'center', marginBottom: 16 }}>
                <a
                  href="https://www.annualcreditreport.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontFamily: 'var(--font-heading)', fontSize: 13, letterSpacing: 2,
                    textTransform: 'uppercase', textDecoration: 'none',
                    color: '#050403', background: `linear-gradient(135deg, #C9A84C, #8B6914)`,
                    padding: '10px 24px', borderRadius: 4, display: 'inline-block',
                    boxShadow: '0 2px 12px rgba(201,168,76,0.4)',
                  }}
                >
                  Get Your Free Credit Report
                </a>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', marginTop: 6 }}>
                  annualcreditreport.com &middot; Free from all 3 bureaus &middot; No credit card required
                </p>
              </div>
              <CreditReportGuide />
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  )
}

function UploadSlot({ cfg, state, onFile }: { cfg: SlotConfig; state: SlotState; onFile: (f: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)

  function pick() {
    inputRef.current?.click()
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault(); setDrag(false)
        const f = e.dataTransfer.files?.[0]
        if (f) onFile(f)
      }}
      style={{
        display: 'grid',
        gridTemplateColumns: '68px 1fr auto',
        alignItems: 'center',
        gap: 16,
        padding: '16px 18px',
        background: state.armored ? `${ACCENT}0F` : drag ? `${ACCENT}11` : 'rgba(0,0,0,0.4)',
        border: `1px solid ${state.armored ? ACCENT + '66' : drag ? ACCENT + '44' : 'rgba(138,130,120,0.2)'}`,
        borderRadius: 6,
        transition: 'all 0.2s',
      }}
    >
      {/* Armor badge */}
      <div style={{
        width: 56, height: 56, borderRadius: 6,
        border: `2px solid ${state.armored ? ACCENT : '#5A5A5A'}`,
        background: state.armored ? `${ACCENT}22` : 'rgba(0,0,0,0.6)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        boxShadow: state.armored ? `0 0 14px ${ACCENT}66` : 'none',
      }}>
        <span style={{
          fontFamily: 'serif', fontSize: 22,
          color: state.armored ? ACCENT : '#8A8278',
          lineHeight: 1,
        }}>
          {state.armored ? '✓' : cfg.kanji}
        </span>
        <span style={{
          fontFamily: 'var(--font-cinzel), serif', fontSize: 8,
          color: state.armored ? ACCENT : '#8A8278',
          letterSpacing: 1.5, textTransform: 'uppercase', marginTop: 2,
        }}>
          {cfg.armor}
        </span>
      </div>

      {/* Info */}
      <div>
        <p style={{
          fontFamily: 'var(--font-heading)', fontSize: 14, color: '#F0EBE0',
          letterSpacing: 0.5, margin: 0, marginBottom: 2,
        }}>
          {cfg.title}
        </p>
        {state.armored ? (
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: ACCENT, margin: 0 }}>
            ✓ {state.filename || 'Uploaded'} {state.sizeKb > 0 && <span style={{ color: '#8A8278' }}>&middot; {state.sizeKb} KB</span>}
          </p>
        ) : state.uploading ? (
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: ACCENT, margin: 0, fontStyle: 'italic' }}>
            Forging armor...
          </p>
        ) : (
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278', margin: 0 }}>
            {cfg.hint}
          </p>
        )}
        {state.error && (
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: '#FF5A5A', margin: 0, marginTop: 2 }}>
            {state.error}
          </p>
        )}
      </div>

      {/* Action */}
      <div>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.txt,.csv,.docx,.html,.htm"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) onFile(f)
          }}
          style={{ display: 'none' }}
        />
        <button
          onClick={pick}
          disabled={state.uploading}
          style={{
            fontFamily: 'var(--font-heading)', fontSize: 12, letterSpacing: 2,
            textTransform: 'uppercase', color: state.armored ? ACCENT : '#F0EBE0',
            background: state.armored ? 'transparent' : `linear-gradient(135deg, ${ACCENT}, #8B6914)`,
            padding: '8px 18px', borderRadius: 4,
            border: state.armored ? `1px solid ${ACCENT}66` : 'none',
            cursor: state.uploading ? 'wait' : 'pointer',
          }}
        >
          {state.armored ? 'Replace' : state.uploading ? '...' : 'Upload'}
        </button>
      </div>
    </div>
  )
}
