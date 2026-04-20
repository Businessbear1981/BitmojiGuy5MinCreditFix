export type ScenePresetKey =
  | 'landing'
  | 'warrior'
  | 'water'
  | 'wisdom'
  | 'gold'
  | 'nirvana'
  | 'interstitial'
  | 'command'

export interface ScenePreset {
  bg: string
  accent: string
  kanji?: string
  overlay: number
  lighting: {
    color: string
    position: string
    size: string
    intensity: number
  }
  breathing?: {
    color: string
    motif: 'ripples' | 'embers' | 'petals' | 'scrolls' | 'mist'
  }
}

export const PRESETS: Record<ScenePresetKey, ScenePreset> = {
  landing: {
    bg: '/seascape.jpg',
    accent: '#C9A84C',
    overlay: 0.25,
    lighting: {
      color: 'rgba(201,168,76,0.18)',
      position: '20% 18%',
      size: '1000px 700px',
      intensity: 0.7,
    },
  },
  warrior: {
    bg: '/maproom.jpg',
    accent: '#C9A84C',
    kanji: '武',
    overlay: 0.3,
    lighting: {
      color: 'rgba(232,152,68,0.22)',
      position: '18% 15%',
      size: '900px 640px',
      intensity: 0.85,
    },
    breathing: { color: 'rgba(232,152,68,0.08)', motif: 'embers' },
  },
  water: {
    bg: '/koipond-meshy.png',
    accent: '#1D9E75',
    kanji: '水',
    overlay: 0.28,
    lighting: {
      color: 'rgba(29,158,117,0.22)',
      position: '50% 85%',
      size: '1200px 500px',
      intensity: 0.9,
    },
    breathing: { color: 'rgba(29,158,117,0.10)', motif: 'ripples' },
  },
  wisdom: {
    bg: '/scrollroom.jpg',
    accent: '#7F77DD',
    kanji: '智',
    overlay: 0.3,
    lighting: {
      color: 'rgba(127,119,221,0.24)',
      position: '50% 45%',
      size: '900px 700px',
      intensity: 0.8,
    },
    breathing: { color: 'rgba(127,119,221,0.08)', motif: 'scrolls' },
  },
  gold: {
    bg: '/sandgarden.jpg',
    accent: '#EF9F27',
    kanji: '金',
    overlay: 0.28,
    lighting: {
      color: 'rgba(239,159,39,0.28)',
      position: '50% 75%',
      size: '1100px 600px',
      intensity: 1.0,
    },
    breathing: { color: 'rgba(239,159,39,0.12)', motif: 'embers' },
  },
  nirvana: {
    bg: '/dragon-gate.png',
    accent: '#D94A3B',
    kanji: '門',
    overlay: 0.3,
    lighting: {
      color: 'rgba(255,160,100,0.28)',
      position: '50% 40%',
      size: '1200px 800px',
      intensity: 1.0,
    },
    breathing: { color: 'rgba(255,140,180,0.10)', motif: 'petals' },
  },
  interstitial: {
    bg: '/interstitial.jpg',
    accent: '#C9A84C',
    overlay: 0.35,
    lighting: {
      color: 'rgba(201,168,76,0.25)',
      position: '50% 50%',
      size: '800px 800px',
      intensity: 1.0,
    },
    breathing: { color: 'rgba(201,168,76,0.08)', motif: 'mist' },
  },
  command: {
    bg: '/wartable.jpg',
    accent: '#B0701C',
    overlay: 0.32,
    lighting: {
      color: 'rgba(176,112,28,0.26)',
      position: '50% 50%',
      size: '900px 600px',
      intensity: 0.85,
    },
    breathing: { color: 'rgba(176,112,28,0.08)', motif: 'scrolls' },
  },
}
