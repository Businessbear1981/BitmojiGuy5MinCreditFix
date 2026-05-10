---
name: remotion-video
description: Create programmatic video compositions with Remotion. Use when the user wants to build marketing videos, animations, credit-fix walkthroughs, or any video generated from React components. Triggers on "/remotion-video", "make a video", "render a composition", or mentions of Remotion, Remotion Studio, or video compositions.
---

# Remotion Video Workflow

Build videos as React components. Remotion renders TSX compositions to MP4/WebM using headless Chrome.

## Project location

`C:/Users/sgill/BitmojiGuy_CreditFix_FULL/remotion-video/` — scaffolded via `npx create-video@latest`.

Key paths:
- `src/Root.tsx` — registers all compositions
- `src/Composition.tsx` — individual composition component
- `remotion.config.ts` — render config (codec, concurrency, chromium flags)

## Common commands

Run from `remotion-video/` directory:

| Command | Purpose |
|---|---|
| `npm run dev` | Launch Remotion Studio (live preview on localhost:3000) |
| `npm run build` / `npx remotion render <id>` | Render composition to MP4 (default: `out/video.mp4`) |
| `npx remotion still <id> out.png --frame=30` | Render single frame as image |
| `npx remotion compositions` | List all registered compositions |
| `npx remotion render <id> --codec=h264 --crf=18` | Custom encoding |

## Building a composition

```tsx
// src/MyScene.tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion'

export const MyScene: React.FC<{ title: string }> = ({ title }) => {
  const frame = useCurrentFrame()
  const { fps, durationInFrames } = useVideoConfig()

  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' })
  const scale = spring({ frame, fps, config: { damping: 12 } })

  return (
    <AbsoluteFill style={{ background: '#0A0806', color: '#F0D080', fontFamily: 'Inter' }}>
      <div style={{ opacity, transform: `scale(${scale})`, margin: 'auto', fontSize: 80 }}>
        {title}
      </div>
    </AbsoluteFill>
  )
}
```

Then register in `src/Root.tsx`:

```tsx
import { Composition } from 'remotion'
import { MyScene } from './MyScene'

export const RemotionRoot = () => (
  <Composition
    id="MyScene"
    component={MyScene}
    durationInFrames={150}   // 5 seconds at 30 fps
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{ title: 'Hello' }}
  />
)
```

## Core API

- `useCurrentFrame()` — current frame index, drives animation
- `useVideoConfig()` — `{ fps, durationInFrames, width, height }`
- `interpolate(frame, [fromFrames], [toValues], options)` — linear tween
- `spring({ frame, fps, config })` — physics-based ease (0→1)
- `Sequence` — offsets a child by N frames; lets children have own timeline
- `Series` / `Series.Sequence` — stack compositions back-to-back
- `Audio`, `Video`, `Img`, `OffthreadVideo` — media elements
- `staticFile('filename.mp3')` — reference files in `public/`

## Credit-fix project patterns

For BitmojiGuy 5-Min Credit Fix marketing/explainer videos:

**Palette:** Match the app — `#0A0806` backgrounds, `#C9A84C` gold accents, `#F0D080` highlights, `#1D9E75` success green.

**Typography:** Cinzel Decorative for headings, Inter/DM Sans for body. Load via `@remotion/google-fonts`.

**Common scene types:**
1. **Title card** — animated logo + product name + tagline
2. **Feature walkthrough** — 5-step numbered flow matching app steps (Warrior → Water → Wisdom → Gold → Nirvana)
3. **Testimonial** — quote on parchment-style bg with portrait
4. **Price reveal** — $24.99 animated entrance with CTA
5. **Demo capture** — screen recording (`OffthreadVideo`) with overlayed callouts

**Render presets for social:**
- Instagram square: `1080x1080`, 30 fps, 30s max
- TikTok/Reels vertical: `1080x1920`, 30 fps, 60s max
- YouTube landscape: `1920x1080`, 30 fps, any length

## When to invoke

Invoke this skill when the user:
- Says "make a video", "create a composition", "render this"
- Types `/remotion-video`
- Asks to animate something, add motion graphics, or create a demo video
- Mentions Remotion, frames, fps, compositions, video rendering

## Checklist before rendering

- [ ] Composition registered in `src/Root.tsx` with unique `id`
- [ ] `durationInFrames`, `fps`, `width`, `height` all set
- [ ] Assets in `public/` (not `src/`)
- [ ] `npm run dev` used to preview first
- [ ] For long renders: set `--concurrency=1` if RAM-constrained (this laptop has 8 GB)
