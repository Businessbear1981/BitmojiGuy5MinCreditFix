'use client';

import { useState } from 'react';
import { Card, CardTitle, CardSub } from '../ui/Card';
import { Input, Select } from '../ui/Input';
import { Button } from '../ui/Button';
import { BitmojiFigure } from '../BitmojiFigure';
import { US_STATES } from '@/lib/types';
import { startSession } from '@/lib/api';

interface Props {
  onComplete: () => void;
}

export function StepInfo({ onComplete }: Props) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [state, setState] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!name || !email) return setError('Name and email are required');
    if (!state) return setError('Please select your state — it adds state law citations to your letters');
    setError('');
    setLoading(true);
    try {
      await startSession(name, email, phone, state);
      onComplete();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-6 items-start">
      <BitmojiFigure pose="crossed" />
      <div className="flex-1 min-w-0">
        {/* Cherry blossom petal BG */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-xl -z-10">
          {Array.from({ length: 12 }).map((_, i) => (
            <div
              key={i}
              className="absolute w-2.5 h-2.5 rounded-[50%_0_50%_0] opacity-0 animate-[petalFall_8s_linear_infinite]"
              style={{
                left: `${Math.random() * 100}%`,
                background: `radial-gradient(ellipse, rgba(220,180,200,0.6), rgba(180,140,160,0.2))`,
                animationDuration: `${6 + Math.random() * 6}s`,
                animationDelay: `${-Math.random() * 10}s`,
              }}
            />
          ))}
        </div>

        <Card className="!bg-[rgba(8,8,12,0.95)] !border-[rgba(200,170,190,0.12)] relative z-10">
          <CardTitle className="!text-[#E8D5E0] !drop-shadow-[0_0_12px_rgba(200,170,190,0.3)]">
            Let&apos;s Go
          </CardTitle>
          <CardSub>Enter your info to start your dispute package.</CardSub>
          <Input label="Full Name" placeholder="Your full legal name" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
          <Input label="Email" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
          <Input label="Phone (optional)" type="tel" placeholder="(555) 123-4567" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel" />
          <Select
            label="State"
            value={state}
            onChange={(e) => setState(e.target.value)}
            options={[{ value: '', label: 'Select your state...' }, ...US_STATES]}
          />
          {error && <p className="text-sm text-red-400 mb-3">{error}</p>}
          <Button full onClick={handleSubmit} disabled={loading}>
            {loading ? 'Starting...' : 'Start My Credit Fix'}
          </Button>
        </Card>
      </div>
    </div>
  );
}
