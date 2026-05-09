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
  // Doors start OPEN so initial page is interactive immediately
  const [shojiOpen, setShojiOpen] = useState(true)
  const router = useRouter()
  const pathname = usePathname()
  const isClosing = useRef(false)

  // Always open doors after any route change — regardless of how we got there
  useEffect(() => {
    // Small delay so the new page has mounted
    const t = setTimeout(() => {
      isClosing.current = false
      setShojiOpen(true)
    }, 60)
    return () => clearTimeout(t)
  }, [pathname])

  const navigateTo = useCallback((path: string) => {
    if (isClosing.current) return
    if (path === pathname) return

    isClosing.current = true
    // Close doors
    setShojiOpen(false)

    // Wait for close animation, then navigate
    setTimeout(() => {
      router.push(path)
    }, 700)
  }, [router, pathname])

  return (
    <ShojiNavContext.Provider value={{ shojiOpen, setShojiOpen, navigateTo }}>
      {children}
    </ShojiNavContext.Provider>
  )
}
