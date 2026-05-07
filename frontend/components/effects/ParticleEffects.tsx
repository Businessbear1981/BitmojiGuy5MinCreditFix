'use client'

import { useEffect, useState } from 'react'

interface Particle {
  id: string
  type: 'cherry' | 'dust' | 'spark'
  x: number
  y: number
  duration: number
  delay: number
}

export function ParticleEffects() {
  const [particles, setParticles] = useState<Particle[]>([])

  useEffect(() => {
    // Generate cherry blossoms continuously
    const cherryInterval = setInterval(() => {
      const newParticle: Particle = {
        id: `cherry-${Date.now()}-${Math.random()}`,
        type: 'cherry',
        x: Math.random() * 100,
        y: -5,
        duration: 8 + Math.random() * 4,
        delay: 0,
      }
      setParticles((prev) => [...prev, newParticle])

      // Clean up old particles
      setTimeout(() => {
        setParticles((prev) => prev.filter((p) => p.id !== newParticle.id))
      }, (newParticle.duration + newParticle.delay) * 1000)
    }, 800)

    return () => clearInterval(cherryInterval)
  }, [])

  return (
    <div className="particle-container">
      {particles.map((particle) => (
        <div
          key={particle.id}
          className={`particle particle-${particle.type}`}
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            '--tx': `${(Math.random() - 0.5) * 100}px`,
            animationDuration: `${particle.duration}s`,
            animationDelay: `${particle.delay}s`,
          } as React.CSSProperties & { '--tx': string }}
        />
      ))}
    </div>
  )
}
