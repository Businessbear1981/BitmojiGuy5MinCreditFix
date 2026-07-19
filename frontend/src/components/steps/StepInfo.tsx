'use client';

import { useState } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Input, Select } from '../ui/Input';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { BETA_STATES, US_STATES } from '@/lib/types';
import { acceptTerms, createCase, ApiError } from '@/lib/api';
import { saveSession } from '@/lib/session';

interface Props {
  onComplete: (sessionId: string, region: string) => void;
}

export function StepInfo({ onComplete }: Props) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [street, setStreet] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [zip, setZip] = useState('');
  const [dob, setDob] = useState('');
  const [ssnLast4, setSsnLast4] = useState('');
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!name.trim() || !email.trim()) return setError('Name and email are required');
    if (!street.trim() || !city.trim() || !state || !/^\d{5}(-\d{4})?$/.test(zip.trim()))
      return setError('Full mailing address with a valid ZIP code is required — your letters are mailed from it');
    if (!dob) return setError('Date of birth is required — the bureaus use it to locate your file');
    if (!/^\d{4}$/.test(ssnLast4)) return setError('Enter the last 4 digits of your SSN');
    if (!phone.trim()) return setError('Phone number is required');
    if (!consent) return setError('Please review and accept the terms to continue');
    if (!(BETA_STATES as readonly string[]).includes(state)) {
      return setError(
        `Beta launch is limited to Texas, California, and Washington — ${state} isn’t open yet.`,
      );
    }

    setError('');
    setLoading(true);
    try {
      // Consent gate: a signed terms token is required to open a case
      const { terms_token } = await acceptTerms();
      const address = `${street.trim()}, ${city.trim()}, ${state} ${zip.trim()}`;
      const data = await createCase(
        { name: name.trim(), address, dob, ssn_last4: ssnLast4, phone: phone.trim(), email: email.trim() },
        terms_token,
      );
      saveSession(data.session_id);
      onComplete(data.session_id, data.region);
    } catch (e: unknown) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong — please try again');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-6 items-start">
      <BitmojiFigure pose="crossed" />
      <div className="flex-1 min-w-0">
        <Card className="!bg-[rgba(8,8,12,0.95)] !border-[rgba(200,170,190,0.12)] relative z-10">
          <CardTitle className="!text-[#E8D5E0] !drop-shadow-[0_0_12px_rgba(200,170,190,0.3)]">
            Let&apos;s Go
          </CardTitle>
          <CardSub>
            Your dispute letters are legal documents — the bureaus need this info to
            locate your file. It&apos;s encrypted and automatically deleted within 24 hours.
          </CardSub>

          <Input label="Full Legal Name" placeholder="Your full legal name" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />

          <div className="grid grid-cols-1 sm:grid-cols-2 sm:gap-3">
            <Input label="Email" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
            <Input label="Phone" type="tel" placeholder="(555) 123-4567" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel" />
          </div>

          <Input label="Street Address" placeholder="123 Main St, Apt 4" value={street} onChange={(e) => setStreet(e.target.value)} autoComplete="street-address" />
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_1fr_120px] sm:gap-3">
            <Input label="City" placeholder="Dallas" value={city} onChange={(e) => setCity(e.target.value)} autoComplete="address-level2" />
            <Select
              label="State"
              value={state}
              onChange={(e) => setState(e.target.value)}
              options={[{ value: '', label: 'Select...' }, ...US_STATES]}
            />
            <Input label="ZIP" placeholder="75201" inputMode="numeric" value={zip} onChange={(e) => setZip(e.target.value)} autoComplete="postal-code" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 sm:gap-3">
            <Input label="Date of Birth" type="date" value={dob} onChange={(e) => setDob(e.target.value)} autoComplete="bday" />
            <Input
              label="SSN — Last 4 Digits"
              placeholder="1234"
              inputMode="numeric"
              maxLength={4}
              value={ssnLast4}
              onChange={(e) => setSsnLast4(e.target.value.replace(/\D/g, ''))}
            />
          </div>

          <div className="bg-teal-400/[0.03] border border-teal-400/[0.12] rounded-lg px-4 py-3 mb-4 text-[12px] leading-relaxed text-gray-400">
            Beta launch is limited to <strong className="text-teal-400">Texas, California, and Washington</strong>.
            We&apos;ll check your ZIP automatically.
          </div>

          {/* Consent / disclaimer gate */}
          <label className="flex items-start gap-3 cursor-pointer bg-purple-500/[0.04] border border-purple-500/15 rounded-lg px-4 py-3.5 mb-4">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-0.5 w-4 h-4 accent-purple-500 shrink-0"
            />
            <span className="text-[12px] leading-relaxed text-gray-400">
              I understand this is a <strong className="text-gray-300">self-help document preparation tool</strong>,
              not legal advice or credit repair services; AE Labs is not a law firm. I authorize AE Labs to
              prepare dispute letters from the information and documents I provide, and I understand my data
              is encrypted and permanently deleted within 24 hours. I agree to the{' '}
              <a href="/terms" target="_blank" className="underline text-gray-300">Terms of Service</a> and{' '}
              <a href="/privacy" target="_blank" className="underline text-gray-300">Privacy Policy</a>.
            </span>
          </label>

          {error && <p className="text-sm text-red-400 mb-3" role="alert">{error}</p>}
          <Button full onClick={handleSubmit} disabled={loading}>
            {loading ? 'Starting...' : 'Start My Credit Fix'}
          </Button>
        </Card>
      </div>
    </div>
  );
}
