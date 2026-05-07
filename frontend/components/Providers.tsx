'use client'

import { ShojiNavProvider, useShojiNav } from '@/lib/shojiNav'
import { ShojiDoors } from '@/components/shoji/ShojiDoors'
import { ParticleEffects } from '@/components/effects/ParticleEffects'
import { CinematicVignette } from '@/components/effects/CinematicVignette'

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
        <ParticleEffects />
        {children}
        <GlobalDoors />
        <CinematicVignette intensity={0.5} animated={true} />
      </div>
    </ShojiNavProvider>
  )
}
