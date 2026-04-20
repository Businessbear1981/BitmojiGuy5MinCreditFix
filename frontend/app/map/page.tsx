'use client'

import { useState } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
import { TopNav } from '@/components/nav/TopNav'
import { WizardSidebar } from '@/components/sidebar/WizardSidebar'
import { submitIntake } from '@/lib/api'

const STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
  'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
  'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
  'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC',
]

const REFERRAL_SOURCES = [
  { value: '', label: 'Select...' },
  { value: 'snapchat', label: 'Snapchat' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'direct_email', label: 'Direct Email' },
  { value: 'other', label: 'Other' },
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
    state: '',
    referralSource: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const update = (k: keyof typeof formData, v: string) =>
    setFormData((prev) => ({ ...prev, [k]: v }))

  async function handleSubmit() {
    setError('')
    if (!formData.firstName || !formData.lastName) {
      setError('First and last name are required.')
      return
    }
    if (!formData.email) {
      setError('Email is required.')
      return
    }
    if (!formData.phone) {
      setError('Phone number is required.')
      return
    }
    if (!formData.state) {
      setError('Please select your state.')
      return
    }

    setSubmitting(true)
    try {
      const res = await submitIntake({
        name: `${formData.firstName} ${formData.lastName}`.trim(),
        email: formData.email,
        phone: formData.phone,
        address: formData.address,
        state: formData.state,
        referral_source: formData.referralSource,
      })
      const data = await res.json()
      if (data.ok) {
        navigateTo('/dojo')
      } else {
        setError(data.error || 'Something went wrong. Try again.')
      }
    } catch {
      setError('Could not connect to server. Try again.')
    }
    setSubmitting(false)
  }

  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/maproom.png"
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
        <TopNav currentStep={1} />
        <div style={{ flex: 1, display: 'flex' }}>
          <WizardSidebar step={1} />

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
                Step 1 of 7 &middot; 地 &middot; The Map Room
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
                    placeholder="John"
                    value={formData.firstName}
                    onChange={(e) => update('firstName', e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>Last Name</label>
                  <input type="text" style={inputStyle}
                    placeholder="Doe"
                    value={formData.lastName}
                    onChange={(e) => update('lastName', e.target.value)} />
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={labelStyle}>Mailing Address</label>
                  <input type="text" style={inputStyle}
                    placeholder="123 Main St, City, ST 00000"
                    value={formData.address}
                    onChange={(e) => update('address', e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>Phone</label>
                  <input type="tel" style={inputStyle}
                    placeholder="(555) 555-0000"
                    value={formData.phone}
                    onChange={(e) => update('phone', e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>Email</label>
                  <input type="email" style={inputStyle}
                    placeholder="you@email.com"
                    value={formData.email}
                    onChange={(e) => update('email', e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>State</label>
                  <select style={selectStyle}
                    value={formData.state}
                    onChange={(e) => update('state', e.target.value)}>
                    <option value="">Select state...</option>
                    {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>How Did You Find Us?</label>
                  <select style={selectStyle}
                    value={formData.referralSource}
                    onChange={(e) => update('referralSource', e.target.value)}>
                    {REFERRAL_SOURCES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </select>
                </div>
              </div>

              {error && (
                <p style={{
                  marginTop: 16, padding: '10px 14px',
                  background: 'rgba(255,60,60,0.1)', border: '1px solid rgba(255,60,60,0.3)',
                  borderRadius: 4, color: '#FF6B6B',
                  fontFamily: 'var(--font-body)', fontSize: 13,
                }}>
                  {error}
                </p>
              )}

              <div style={{ marginTop: 28, display: 'flex', justifyContent: 'center' }}>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  style={{
                    fontFamily: 'var(--font-cinzel), serif',
                    fontSize: 14,
                    fontWeight: 700,
                    letterSpacing: 3,
                    textTransform: 'uppercase',
                    color: '#1A0A02',
                    background: submitting
                      ? 'rgba(100,100,100,0.3)'
                      : 'linear-gradient(135deg, #8B6914, #F0D080)',
                    padding: '0.95rem 2.5rem',
                    borderRadius: 4,
                    border: '1px solid #8B5A20',
                    cursor: submitting ? 'wait' : 'pointer',
                    boxShadow: submitting ? 'none' : '0 4px 30px rgba(201,168,76,0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
                    opacity: submitting ? 0.6 : 1,
                  }}
                >
                  {submitting ? 'Submitting...' : 'Continue \u2192'}
                </button>
              </div>
            </div>
          </div>
        </div>
    </div>
    </>
  )
}
