'use client';

import { useState } from 'react';
import { Header } from '@/components/Header';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FishbowlRegion {
  name: string;
  current: number;
  limit: number;
  available: number;
  utilization: number;
}

interface AdminStats {
  total_cases: number;
  paid_cases: number;
  revenue_estimate: string;
  today: number;
  fishbowl: Record<string, FishbowlRegion>;
}

export default function AdminPage() {
  const [key, setKey] = useState('');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/admin/stats`, {
        headers: { 'X-Admin-Key': key },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `Request failed (${res.status})`);
      }
      setStats(await res.json());
    } catch (e) {
      setStats(null);
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Header />
      <div className="relative z-[5] max-w-[720px] mx-auto px-5 py-10 pb-20">
        <h1 className="font-bangers text-[36px] tracking-wider text-teal-400 drop-shadow-[0_0_12px_rgba(0,212,212,0.3)] mb-6">
          Admin
        </h1>

        <Card>
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="block text-[12px] text-gray-500 mb-1.5">Admin key</label>
              <input
                type="password"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && key && load()}
                className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[14px] text-gray-200 focus:outline-none focus:border-teal-400/50"
                placeholder="X-Admin-Key"
              />
            </div>
            <Button onClick={load} disabled={!key || loading}>
              {loading ? 'Loading…' : 'Load stats'}
            </Button>
          </div>
          {error && <p className="mt-3 text-[13px] text-red-400">{error}</p>}
        </Card>

        {stats && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-2">
              {[
                { label: 'Total cases', value: String(stats.total_cases) },
                { label: 'Paid', value: String(stats.paid_cases) },
                { label: 'Revenue (est.)', value: stats.revenue_estimate },
                { label: 'Today', value: String(stats.today) },
              ].map((m) => (
                <div
                  key={m.label}
                  className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center"
                >
                  <div className="text-[22px] font-bold text-teal-400">{m.value}</div>
                  <div className="text-[11px] text-gray-500 mt-1">{m.label}</div>
                </div>
              ))}
            </div>

            <Card className="mt-4">
              <h2 className="text-[15px] font-bold text-gray-200 mb-3">Beta regions (fishbowl)</h2>
              <div className="space-y-2">
                {Object.entries(stats.fishbowl).map(([region, r]) => (
                  <div key={region} className="flex items-center gap-3 text-[13px]">
                    <span className="w-10 font-mono text-gray-300">{region}</span>
                    <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                      <div
                        className="h-full bg-teal-400/70"
                        style={{ width: `${Math.min(100, r.utilization)}%` }}
                      />
                    </div>
                    <span className="text-gray-500 w-20 text-right">
                      {r.current}/{r.limit}
                    </span>
                    <span className={r.available > 0 ? 'text-teal-400' : 'text-red-400'}>
                      {r.available > 0 ? 'open' : 'full'}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}
      </div>
    </>
  );
}
