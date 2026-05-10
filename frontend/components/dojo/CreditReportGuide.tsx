'use client'

import { useState, useEffect } from 'react'
import { ExternalLink, CheckCircle, AlertCircle } from 'lucide-react'

const FLASK = process.env.NEXT_PUBLIC_FLASK_URL ?? 'http://localhost:5000'
const GOLD = '#C9A84C'

interface Guide {
  title: string
  description: string
  bureaus: string[]
  steps: Array<{
    number: number
    title: string
    description: string
    action?: string
    link?: string
    warning?: string
    tip?: string
  }>
  phone_number: string
  mail_address: string
  faq: Array<{
    question: string
    answer: string
  }>
}

interface Bureaus {
  [key: string]: {
    phone: string
    website: string
    dispute_url: string
  }
}

export function CreditReportGuide() {
  const [guide, setGuide] = useState<Guide | null>(null)
  const [bureaus, setBureaus] = useState<Bureaus | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null)

  useEffect(() => {
    const fetchGuide = async () => {
      try {
        const [guideRes, bureauxRes] = await Promise.all([
          fetch(`${FLASK}/api/credit-report-guide`),
          fetch(`${FLASK}/api/credit-report-bureaus`),
        ])

        if (guideRes.ok) {
          const data = await guideRes.json()
          setGuide(data.guide)
        }

        if (bureauxRes.ok) {
          const data = await bureauxRes.json()
          setBureaus(data.bureaus)
        }
      } catch (err) {
        console.error('Error fetching credit report guide:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchGuide()
  }, [])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: GOLD }}>
        ⏳ Loading credit report guide...
      </div>
    )
  }

  if (!guide) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#f44336' }}>
        ⚠️ Could not load guide
      </div>
    )
  }

  return (
    <div
      style={{
        background: 'rgba(12,8,4,0.9)',
        border: `1px solid ${GOLD}`,
        borderRadius: 8,
        padding: '2rem',
        color: '#F0EBE0',
      }}
    >
      {/* Header */}
      <h2 style={{ color: GOLD, marginBottom: '0.5rem', fontSize: '1.5rem' }}>
        {guide.title}
      </h2>
      <p style={{ color: '#999', marginBottom: '2rem', fontSize: '0.95rem' }}>
        {guide.description}
      </p>

      {/* Steps */}
      <div style={{ marginBottom: '3rem' }}>
        <h3 style={{ color: GOLD, marginBottom: '1.5rem', fontSize: '1.1rem' }}>
          📋 Step-by-Step Guide
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {guide.steps.map((step) => (
            <div
              key={step.number}
              style={{
                display: 'flex',
                gap: '1.5rem',
                padding: '1.5rem',
                background: 'rgba(201,168,76,0.05)',
                border: `1px solid rgba(201,168,76,0.2)`,
                borderRadius: 6,
              }}
            >
              {/* Step number */}
              <div
                style={{
                  minWidth: '50px',
                  height: '50px',
                  background: GOLD,
                  color: '#0A0804',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.25rem',
                  fontWeight: 'bold',
                  flexShrink: 0,
                }}
              >
                {step.number}
              </div>

              {/* Step content */}
              <div style={{ flex: 1 }}>
                <h4 style={{ color: GOLD, marginBottom: '0.5rem', fontSize: '1rem' }}>
                  {step.title}
                </h4>
                <p style={{ color: '#CCC', fontSize: '0.95rem', marginBottom: '0.75rem' }}>
                  {step.description}
                </p>

                {step.link && (
                  <a
                    href={step.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      color: '#4CAF50',
                      textDecoration: 'none',
                      fontSize: '0.9rem',
                      fontWeight: 'bold',
                      marginBottom: '0.75rem',
                    }}
                  >
                    Open Website <ExternalLink size={14} />
                  </a>
                )}

                {step.warning && (
                  <div
                    style={{
                      display: 'flex',
                      gap: '0.75rem',
                      padding: '0.75rem',
                      background: 'rgba(255,152,0,0.1)',
                      border: '1px solid rgba(255,152,0,0.3)',
                      borderRadius: 4,
                      marginBottom: '0.75rem',
                      fontSize: '0.85rem',
                      color: '#FFB74D',
                    }}
                  >
                    <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
                    <span>{step.warning}</span>
                  </div>
                )}

                {step.tip && (
                  <div
                    style={{
                      display: 'flex',
                      gap: '0.75rem',
                      padding: '0.75rem',
                      background: 'rgba(76,175,80,0.1)',
                      border: '1px solid rgba(76,175,80,0.3)',
                      borderRadius: 4,
                      fontSize: '0.85rem',
                      color: '#81C784',
                    }}
                  >
                    <CheckCircle size={16} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
                    <span>{step.tip}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bureau Contact Info */}
      {bureaus && (
        <div style={{ marginBottom: '3rem' }}>
          <h3 style={{ color: GOLD, marginBottom: '1.5rem', fontSize: '1.1rem' }}>
            📞 Bureau Contact Information
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {Object.entries(bureaus).map(([name, info]) => (
              <div
                key={name}
                style={{
                  padding: '1.5rem',
                  background: 'rgba(201,168,76,0.05)',
                  border: `1px solid rgba(201,168,76,0.2)`,
                  borderRadius: 6,
                }}
              >
                <h4 style={{ color: GOLD, marginBottom: '1rem', fontSize: '1rem' }}>
                  {name}
                </h4>
                <div style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
                  <div style={{ marginBottom: '0.75rem' }}>
                    <span style={{ color: '#999' }}>📞 Phone:</span>
                    <br />
                    <a
                      href={`tel:${info.phone}`}
                      style={{ color: '#4CAF50', textDecoration: 'none' }}
                    >
                      {info.phone}
                    </a>
                  </div>
                  <div style={{ marginBottom: '0.75rem' }}>
                    <span style={{ color: '#999' }}>🌐 Website:</span>
                    <br />
                    <a
                      href={info.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#4CAF50', textDecoration: 'none' }}
                    >
                      {info.website}
                    </a>
                  </div>
                  <div>
                    <span style={{ color: '#999' }}>📝 Dispute:</span>
                    <br />
                    <a
                      href={info.dispute_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#4CAF50', textDecoration: 'none', fontSize: '0.85rem' }}
                    >
                      Online Dispute Form
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FAQ */}
      <div>
        <h3 style={{ color: GOLD, marginBottom: '1.5rem', fontSize: '1.1rem' }}>
          ❓ Frequently Asked Questions
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {guide.faq.map((item, idx) => (
            <div
              key={idx}
              style={{
                border: `1px solid rgba(201,168,76,0.2)`,
                borderRadius: 6,
                overflow: 'hidden',
              }}
            >
              <button
                onClick={() => setExpandedFaq(expandedFaq === idx ? null : idx)}
                style={{
                  width: '100%',
                  padding: '1rem 1.5rem',
                  background: 'rgba(201,168,76,0.05)',
                  border: 'none',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ color: GOLD, fontWeight: 'bold' }}>
                  {item.question}
                </span>
                <span style={{ color: GOLD, fontSize: '1.2rem' }}>
                  {expandedFaq === idx ? '−' : '+'}
                </span>
              </button>
              {expandedFaq === idx && (
                <div
                  style={{
                    padding: '1rem 1.5rem',
                    background: 'rgba(12,8,4,0.5)',
                    borderTop: `1px solid rgba(201,168,76,0.2)`,
                    color: '#CCC',
                    fontSize: '0.95rem',
                    lineHeight: '1.6',
                  }}
                >
                  {item.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Contact Info */}
      <div
        style={{
          marginTop: '2rem',
          padding: '1.5rem',
          background: 'rgba(201,168,76,0.05)',
          border: `1px solid rgba(201,168,76,0.2)`,
          borderRadius: 6,
          fontSize: '0.9rem',
        }}
      >
        <h4 style={{ color: GOLD, marginBottom: '1rem' }}>📮 Alternative Methods</h4>
        <div style={{ lineHeight: '1.8' }}>
          <div>
            <strong>Phone:</strong> {guide.phone_number}
          </div>
          <div style={{ marginTop: '0.75rem' }}>
            <strong>Mail:</strong>
            <br />
            {guide.mail_address}
          </div>
        </div>
      </div>
    </div>
  )
}
