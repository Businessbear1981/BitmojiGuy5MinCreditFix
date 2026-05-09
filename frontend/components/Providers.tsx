'use client'

import { ShojiNavProvider, useShojiNav } from '@/lib/shojiNav'
import { ShojiDoors } from '@/components/shoji/ShojiDoors'

function GlobalDoors() {
  const { shojiOpen } = useShojiNav()
  return <ShojiDoors isOpen={shojiOpen} />
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ShojiNavProvider>
      <div style={{
        position: 'relative',
        width: '100%',
        minHeight: '100vh',
        overflow: 'hidden',
      }}>
        {children}
        <GlobalDoors />
      </div>
    </ShojiNavProvider>
  )
}
