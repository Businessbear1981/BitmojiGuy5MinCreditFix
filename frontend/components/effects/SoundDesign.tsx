'use client'

import { useEffect, useRef, useState } from 'react'

interface SoundDesignProps {
  sceneKey?: string
  enabled?: boolean
}

export function SoundDesign({ sceneKey = 'landing', enabled = true }: SoundDesignProps) {
  const audioContextRef = useRef<AudioContext | null>(null)
  const oscillatorsRef = useRef<OscillatorNode[]>([])
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    if (!enabled) return

    const initAudio = () => {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      }

      const ctx = audioContextRef.current
      if (ctx.state === 'suspended') {
        ctx.resume()
      }

      setIsInitialized(true)
    }

    // Initialize on first user interaction
    const handleInteraction = () => {
      initAudio()
      document.removeEventListener('click', handleInteraction)
      document.removeEventListener('touchstart', handleInteraction)
    }

    document.addEventListener('click', handleInteraction)
    document.addEventListener('touchstart', handleInteraction)

    return () => {
      document.removeEventListener('click', handleInteraction)
      document.removeEventListener('touchstart', handleInteraction)
    }
  }, [enabled])

  // Play ambient tone based on scene
  useEffect(() => {
    if (!isInitialized || !audioContextRef.current) return

    const ctx = audioContextRef.current
    const masterGain = ctx.createGain()
    masterGain.connect(ctx.destination)
    masterGain.gain.value = 0.05 // Very subtle

    // Scene-specific frequencies (in Hz)
    const frequencies: Record<string, number[]> = {
      landing: [110, 220], // A2, A3 - contemplative
      warrior: [165, 330], // E3, E4 - energetic
      water: [130, 260], // C#3, C#4 - flowing
      wisdom: [174, 349], // F3, F4 - mystical
      gold: [196, 392], // G3, G4 - grounded
      nirvana: [220, 440], // A3, A4 - transcendent
    }

    const baseFreqs = frequencies[sceneKey] || frequencies.landing

    // Create subtle ambient oscillators
    baseFreqs.forEach((freq) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sine'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(0, ctx.currentTime)
      gain.gain.linearRampToValueAtTime(0.02, ctx.currentTime + 2)

      osc.connect(gain)
      gain.connect(masterGain)
      osc.start()

      oscillatorsRef.current.push(osc)
    })

    return () => {
      oscillatorsRef.current.forEach((osc) => {
        try {
          osc.stop()
        } catch (e) {
          // Already stopped
        }
      })
      oscillatorsRef.current = []
      masterGain.disconnect()
    }
  }, [isInitialized, sceneKey])

  return null // This component is audio-only, no visual output
}
