'use client'

import { ShojiNavProvider } from '@/lib/shojiNav'

export function Providers({ children }: { children: React.ReactNode }) {
  return <ShojiNavProvider>{children}</ShojiNavProvider>
}
