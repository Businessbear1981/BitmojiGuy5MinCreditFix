'use client'

import { createContext, useContext, useState, useCallback, useRef, useEffect, ReactNode } from 'react'
import { useRouter, usePathname } from 'next/navigation'

interface ShojiNavContextValue {
  shojiOpen: boolean
  setShojiOpen: (open: boolean) => void
  navigateTo: (path: string) => void
}

const ShojiNavContext = createContext<ShojiNavContextValue>({
  shojiOpen: true,
  setShojiOpen: () => {},
  navigateTo: () => {},
})

export function useShojiNav() {
  return useContext(ShojiNavContext)
}

export function ShojiNavProvider({ children }: { children: ReactNode }) {
  // Doors start CLOSED so they can open on initial load
  const [shojiOpen, setShojiOpen] = useState(false)
  const router = useRouter()
  const pathname = usePathname()
  const isClosing = useRef(false)

  // Always open doors after any route change — regardless of how we got there
  useEffect(() => {
    // Keep doors closed briefly to show the opening animation
    const t = setTimeout(() => {
      isClosing.current = false
      setShojiOpen(true)
    }, 300)  // Increased delay to let doors stay closed longer
    return () => clearTimeout(t)
  }, [pathname])

  const navigateTo = useCallback((path: string) => {
    if (isClosing.current) return
    if (path === pathname) return

    isClosing.current = true
    // Close doors
    setShojiOpen(false)

    // Wait for close animation (1.1s from ShojiDoors DURATION), then navigate
    setTimeout(() => {
      router.push(path)
    }, 1100)
  }, [router, pathname])

  return (
    <ShojiNavContext.Provider value={{ shojiOpen, setShojiOpen, navigateTo }}>
      {children}
    </ShojiNavContext.Provider>
  )
}
