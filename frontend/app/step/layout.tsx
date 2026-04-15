'use client'

import { ShojiDoors } from '@/components/shoji/ShojiDoors'
import { useShojiNav } from '@/lib/shojiNav'

export default function StepLayout({ children }: { children: React.ReactNode }) {
  const { shojiOpen } = useShojiNav()

  return (
    <div style={{ position: 'relative', width: '100%', minHeight: '100vh', overflow: 'hidden' }}>
      {children}
      <ShojiDoors isOpen={shojiOpen} />
    </div>
  )
}
