'use client'

import { useState } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { SceneLayout } from '@/components/scene/SceneLayout'
import { submitIntake } from '@/lib/api'

const STATES = ['CA', 'TX', 'WA', 'Other']
const BUREAUS = ['All Three', 'Equifax', 'TransUnion', 'Experian']
const REASONS = [
  'Identity theft',
  'Account not mine',
  'Incorrect balance',
  'Outdated negative item',
  'Duplicate account',
]

const labelStyle: React.CSSProperties = {
  fontFamily: 'var(--font-cinzel), serif',
  fontSize: '0.72rem',
  color: '#C9A84C',
  letterSpacing: 2,
  textTransform: 'uppercase',
  marginBottom: 6,
  display: 'block',
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  background: 'rgba(10,8,4,0.85)',
  border: '1px solid rgba(201,168,76,0.3)',
  borderRadius: 4,
  padding: '10px 14px',
  color: '#F0EBE0',
  fontFamily: 'var(--font-body)',
  fontSize: 14,
  outline: 'none',
}

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  appearance: 'none' as const,
  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23C9A84C' stroke-width='1.5' fill='none'/%3E%3C/svg%3E")`,
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right 12px center',
  paddingRight: 32,
}

export default function Step1Page() {
  const { navigateTo } = useShojiNav()
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    address: '',
    phone: '',
    email: '',
    state: 'CA',
    bureau: 'All Three',
    disputeReason: 'Identity theft',
  })

  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const update = (k: keyof typeof formData, v: string) =>
    setFormData((prev) => ({ ...prev, [k]: v }))

  async function handleSubmit() {
    if (!formData.firstName || !formData.email) return
    setSubmitting(true)
    try {
      await submitIntake({
        name: `${formData.firstName} ${formData.lastName}`.trim(),
        email: formData.email,
        phone: formData.phone,
        address: formData.address,
        state: formData.state,
      })
    } catch {
      setSubmitError('Could not connect to server. Please try again.')
      setSubmitting(false)
      return
    }
    setSubmitting(false)
    navigateTo('/dojo')
  }

  return (
    <SceneLayout preset="warrior">
        <TopNav currentStep={1} />
        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar step={1} />

          {/* Main panel */}
          <div style={{
            flex: 1,
            padding: '2.5rem',
            background: 'rgba(12,8,4,0.25)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}>
            <div style={{ width: '100%', maxWidth: 640 }}>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 12, color: '#C9A84C',
                letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4,
              }}>
                Step 1 of 7 &middot; 地 &middot; The Adventurer&rsquo;s Intake
              </p>
              <h2 style={{
                fontFamily: 'var(--font-cinzel-decorative), serif',
                fontSize: '1.6rem',
                color: '#F0EBE0',
                letterSpacing: 2,
                marginTop: 0,
                marginBottom: 22,
                textShadow: '0 0 24px rgba(201,168,76,0.3)',
              }}>
                Chart Your Course
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem 1.2rem' }}>
                <div>
                  <label style={labelStyle}>First Name</label>
                  <input type="text" style={inputStyle}
                    value={formData.firstName}
                    onChange={(e) => update('firstName', e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>Last Name</label>
                  <input type="text" style={inputStyle}
                    value={formData.lastName}
                    onChange={(e) => update('lastName', e.target.value)} />
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={labelStyle}>Address</label>
                  <input type="text" style={inputStyle}
                    value={formData.address}
                    onChange={(e) => update('address', e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>Phone</label>
                  <input type="tel" style={inputStyle}
                    value={formData.phone}
                    onChange={(e) => update('phone', e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>Email</label>
                  <input type="email" style={inputStyle}
                    value={formData.email}
                    onChange={(e) => update('email', e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>State</label>
                  <select style={selectStyle}
                    value={formData.state}
                    onChange={(e) => update('state', e.target.value)}>
                    {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Bureau</label>
                  <select style={selectStyle}
                    value={formData.bureau}
                    onChange={(e) => update('bureau', e.target.value)}>
                    {BUREAUS.map((b) => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={labelStyle}>Dispute Reason</label>
                  <select style={selectStyle}
                    value={formData.disputeReason}
                    onChange={(e) => update('disputeReason', e.target.value)}>
                    {REASONS.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
              </div>

              {submitError && <p style={{ color: '#FF5A5A', fontFamily: 'var(--font-body)', fontSize: 13, textAlign: 'center', marginTop: 12 }}>{submitError}</p>}
              <div style={{ marginTop: 28, display: 'flex', justifyContent: 'center' }}>
                <button
                  onClick={handleSubmit}
                  disabled={submitting || !formData.firstName || !formData.email}
                  style={{
                    fontFamily: 'var(--font-cinzel), serif',
                    fontSize: 14,
                    fontWeight: 700,
                    letterSpacing: 3,
                    textTransform: 'uppercase',
                    color: '#1A0A02',
                    background: 'linear-gradient(135deg, #8B6914, #F0D080)',
                    padding: '0.95rem 2.5rem',
                    borderRadius: 4,
                    border: '1px solid #8B5A20',
                    cursor: submitting ? 'wait' : 'pointer',
                    boxShadow: '0 4px 30px rgba(201,168,76,0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
                    opacity: submitting ? 0.7 : 1,
                  }}
                >
                  {submitting ? 'Submitting...' : 'Continue \u2192'}
                </button>
              </div>
            </div>
          </div>
        </div>
    </SceneLayout>
  )
}
