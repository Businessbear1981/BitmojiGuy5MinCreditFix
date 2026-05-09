'use client'

import { useState } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { useWizardStore } from '@/store/wizardStore'
import { SceneLayout } from '@/components/scene/SceneLayout'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { submitIntake } from '@/lib/api'

const STATES = ['CA', 'TX', 'WA', 'FL', 'NY', 'IL', 'GA', 'NC', 'OH', 'PA', 'Other']
const BUREAUS = ['Equifax', 'TransUnion', 'Experian', 'All Three']
const REASONS = [
  'Identity theft',
  'Account not mine',
  'Incorrect balance',
  'Outdated negative item',
  'Duplicate account',
]

const inputStyle: React.CSSProperties = {
  width: '100%',
  background: 'rgba(10,8,4,0.8)',
  border: '1px solid rgba(201,168,76,0.25)',
  borderRadius: 4,
  padding: '10px 14px',
  color: '#F0EBE0',
  fontFamily: 'var(--font-body)',
  fontSize: 14,
  outline: 'none',
  transition: 'border-color 0.2s',
}

const labelStyle: React.CSSProperties = {
  fontFamily: 'var(--font-cinzel), serif',
  fontSize: '0.7rem',
  color: '#C9A84C',
  letterSpacing: 2,
  textTransform: 'uppercase',
  marginBottom: 4,
  display: 'block',
}

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  appearance: 'none' as const,
  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238A8278' stroke-width='1.5' fill='none'/%3E%3C/svg%3E")`,
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right 12px center',
}

export default function Step1Page() {
  const { navigateTo } = useShojiNav()
  const { formData, setFormData } = useWizardStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!formData.firstName || !formData.lastName) {
      return setError('First and last name are required')
    }
    if (!formData.state) return setError('Select your state')
    if (!formData.bureau) return setError('Select target bureau')
    if (!formData.disputeReason) return setError('Select dispute reason')

    setError('')
    setLoading(true)
    try {
      const res = await submitIntake({
        name: `${formData.firstName} ${formData.lastName}`,
        email: '',
        phone: '',
        state: formData.state,
        address: formData.address,
        bureau: formData.bureau,
        disputeReason: formData.disputeReason,
      })
      if (!res.ok) throw new Error('Intake submission failed')
      navigateTo('/step/3')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SceneLayout preset="warrior">
        <TopNav currentStep={2} />

        {/* Zen strip */}
        <div style={{
          padding: '8px 24px', textAlign: 'center',
          background: 'rgba(201,168,76,0.04)', borderBottom: '1px solid rgba(201,168,76,0.1)',
          fontFamily: 'var(--font-heading)', fontSize: 12, fontStyle: 'italic',
          color: '#C9A84C', letterSpacing: 2,
        }}>
          &ldquo;The warrior who dresses with intention fights with precision. Each piece of armor is a vow.&rdquo;
        </div>

        {/* Main content */}
        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar
            step={1}
            mascotSpeech="Name your enemy. State your case. The warrior who knows himself cannot be defeated."
          />

          {/* Main panel */}
          <div style={{
            flex: 1, padding: '2rem',
            background: 'rgba(20,14,8,0.25)',
          }}>
            {/* Step header */}
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 12, color: '#C9A84C',
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4,
            }}>
              Step 1 of 5 &middot; 武 &middot; Samurai Dresses
            </p>
            <h2 style={{
              fontFamily: 'var(--font-heading)', fontSize: '1.4rem', color: '#F0EBE0',
              letterSpacing: 2, marginBottom: 6,
            }}>
              Personal Information
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 13, color: '#8A8278',
              fontStyle: 'italic', marginBottom: 24,
            }}>
              Your identity forges the dispute
            </p>

            {/* Form */}
            <div style={{ maxWidth: 600 }}>
              {/* Row: firstName + lastName */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div>
                  <label style={labelStyle}>First Name</label>
                  <input
                    style={inputStyle}
                    placeholder="First name"
                    value={formData.firstName}
                    onChange={(e) => setFormData({ firstName: e.target.value })}
                    onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(201,168,76,0.5)'}
                    onBlur={(e) => e.currentTarget.style.borderColor = 'rgba(201,168,76,0.25)'}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Last Name</label>
                  <input
                    style={inputStyle}
                    placeholder="Last name"
                    value={formData.lastName}
                    onChange={(e) => setFormData({ lastName: e.target.value })}
                    onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(201,168,76,0.5)'}
                    onBlur={(e) => e.currentTarget.style.borderColor = 'rgba(201,168,76,0.25)'}
                  />
                </div>
              </div>

              {/* Address */}
              <div style={{ marginBottom: 16 }}>
                <label style={labelStyle}>Mailing Address</label>
                <input
                  style={inputStyle}
                  placeholder="Full mailing address"
                  value={formData.address}
                  onChange={(e) => setFormData({ address: e.target.value })}
                  onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(201,168,76,0.5)'}
                  onBlur={(e) => e.currentTarget.style.borderColor = 'rgba(201,168,76,0.25)'}
                />
              </div>

              {/* Row: State + Bureau */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div>
                  <label style={labelStyle}>State</label>
                  <select
                    style={selectStyle}
                    value={formData.state}
                    onChange={(e) => setFormData({ state: e.target.value })}
                  >
                    <option value="" style={{ background: '#0A0806' }}>Select state...</option>
                    {STATES.map((s) => (
                      <option key={s} value={s} style={{ background: '#0A0806' }}>{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Target Bureau</label>
                  <select
                    style={selectStyle}
                    value={formData.bureau}
                    onChange={(e) => setFormData({ bureau: e.target.value })}
                  >
                    <option value="" style={{ background: '#0A0806' }}>Select bureau...</option>
                    {BUREAUS.map((b) => (
                      <option key={b} value={b} style={{ background: '#0A0806' }}>{b}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Dispute Reason */}
              <div style={{ marginBottom: 24 }}>
                <label style={labelStyle}>Dispute Reason</label>
                <select
                  style={selectStyle}
                  value={formData.disputeReason}
                  onChange={(e) => setFormData({ disputeReason: e.target.value })}
                >
                  <option value="" style={{ background: '#0A0806' }}>Select reason...</option>
                  {REASONS.map((r) => (
                    <option key={r} value={r} style={{ background: '#0A0806' }}>{r}</option>
                  ))}
                </select>
              </div>

              {/* Error */}
              {error && (
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#FF4444', marginBottom: 12 }}>
                  {error}
                </p>
              )}

              {/* Nav buttons */}
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <button
                  onClick={() => navigateTo('/')}
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
                  onClick={handleSubmit}
                  disabled={loading}
                  style={{
                    fontFamily: 'var(--font-heading)', fontSize: 14, letterSpacing: 3,
                    textTransform: 'uppercase', color: '#050403',
                    background: 'linear-gradient(135deg, #C9A84C, #8B6914)',
                    padding: '12px 40px', borderRadius: 4, border: 'none',
                    cursor: loading ? 'wait' : 'pointer',
                    boxShadow: '0 4px 20px rgba(201,168,76,0.3)',
                    opacity: loading ? 0.7 : 1,
                  }}
                >
                  {loading ? 'Submitting...' : 'Continue →'}
                </button>
              </div>
            </div>
          </div>
        </div>
    </SceneLayout>
  )
}
