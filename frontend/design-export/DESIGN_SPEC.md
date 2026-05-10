# BitmojiGuy Five-Minute Credit Fix — Complete Design Specification

## Design Philosophy: Cinematic Chanbara Maximalism

This is a **Shogun Warrior Quest** experience. Every screen should feel like a cinematic threshold, not a web form. The user is progressing through enlightenment stages, earning armor, and moving toward release.

---

## Color Palette (OKLCH Format)

### Primary Colors
- **Black Lacquer (Background):** `oklch(0.09 0.008 70)` — Deep, sacred void
- **Parchment Ivory (Foreground):** `oklch(0.92 0.025 82)` — Readable, warm, premium
- **Antique Gold (Primary):** `oklch(0.78 0.13 82)` — Earned authority, earned progress
- **Sea-Mist Blue (Secondary):** `oklch(0.24 0.018 70)` — Calm, contemplative
- **Koi-Jade (Accent):** `oklch(0.76 0.14 82)` — Transformation, life force
- **Temple Crimson (Destructive):** `oklch(0.61 0.22 28)` — Warning, intensity

### Secondary Colors
- **Card Background:** `oklch(0.15 0.015 65 / 82%)` — Slightly lighter than background
- **Muted Text:** `oklch(0.72 0.025 82)` — Secondary information
- **Border:** `oklch(0.8 0.09 82 / 24%)` — Subtle dividers
- **Ring (Focus):** `oklch(0.78 0.13 82)` — Gold focus rings

### Emotional Intent
- Gold = earned, not given
- Black = sacred, not empty
- Mist-blue = vulnerability at start
- Crimson = intensity at finish
- Jade = transformation happening

---

## Typography System

### Font Stack
1. **Cinzel Decorative** — Ceremonial headings (h1, h2, page titles)
2. **Cinzel** — Navigation, ritual labels, subheadings
3. **Rajdhani** — Body copy, technical text, explanations

### Hierarchy Rules
- **H1 (Page Titles):** Cinzel Decorative, 48px, letter-spacing +2px, all-caps
- **H2 (Section Titles):** Cinzel, 32px, letter-spacing +1px
- **H3 (Subsections):** Cinzel, 24px
- **Body Text:** Rajdhani, 16px, line-height 1.6
- **Labels/Buttons:** Rajdhani, 14px, font-weight 600
- **Small Text:** Rajdhani, 12px, opacity 0.8

### Font Import
```html
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Cinzel+Decorative:wght@400;700&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
```

---

## Layout Paradigm

### Three-Column Cinematic Control Room
```
┌─────────────────────────────────────────────────────────┐
│  LEFT RAIL              CENTER STAGE           RIGHT PANEL │
│  (Narrative)            (Warrior)              (5 Paths)   │
│                                                            │
│  • Seascape origin      [Animated Warrior]    • Dojo       │
│  • Story beats          [Armor Progress]      • Koi Pond   │
│  • Watermarks           [Transformation]      • Sand Gdn   │
│  • Emotional arc        [Sparks/Glow]         • Stairway   │
│                                               • Dragon Gate│
└─────────────────────────────────────────────────────────┘
```

### Key Principles
- Asymmetric, not centered
- Left narrative creates emotional context
- Center warrior is the hero (not the form)
- Right panel offers five distinct enlightenment paths
- Negative space is intentional, not wasted

---

## Signature Visual Elements

### 1. Lone Cypress Seascape
- Sacred origin imagery
- Appears on landing/hero section
- Preserved from user's original design
- Emotional anchor for the entire experience

### 2. Rotating Kanji Watermarks
- Glowing seal marks that slowly rotate
- Appear as background texture
- Represent spiritual progression
- Update as user completes stages

### 3. Shoji-Door Transitions
- Sliding panel effects between screens
- Shadow and weight on movement
- Cinematic easing (not bouncy)
- Frame each new threshold

### 4. Armor Progression
- Visual representation of user's credit repair journey
- Starts bare, builds with each document
- Sparks and metallic highlights on upgrade
- Central hero mechanic

### 5. Atmospheric Overlays
- Petals drifting (serenity)
- Embers glowing (intensity)
- Water ripples (reflection)
- Moonlit haze (mystery)

---

## Animation Language

### Easing
- **Transitions:** `cubic-bezier(0.25, 0.46, 0.45, 0.94)` (slow, weighty)
- **Entrance:** 600ms
- **Exit:** 400ms
- **Hover:** 200ms

### Motion Principles
- Slow, intentional, cinematic
- Not bouncy or playful
- Weight and shadow on movement
- Depth created through parallax
- Particles drift at different speeds

### Specific Animations
- **Shoji Doors:** Slide with shadow, 600ms ease-out
- **Watermarks:** Slow rotation (12s), shimmer opacity
- **Armor Pieces:** Materialize with sparks, 800ms ease-out
- **Particles:** Drift at 3-8s duration, varying speeds
- **Glow Effects:** Subtle pulse, 2-3s cycle

---

## Component Specifications

### Hero Section
- Full-width seascape background
- Overlay: semi-transparent black (0.4 opacity)
- Centered title: "Five-Minute Credit Fix"
- Subtitle: "Become the warrior your credit deserves"
- CTA Button: Gold, large, prominent

### Warrior Stage
- Central animated figure
- Armor pieces layer on top as user progresses
- Sparks on upgrade
- Glow effect around completed stages
- Metallic highlights on armor

### Path Selector (Right Panel)
- Five vertical cards
- Each represents a stage
- Gold accent on active path
- Hover: subtle glow, slight lift
- Click: advance to stage

### Form Sections
- Minimal, clean layout
- Gold accent on focused inputs
- Subtle borders (24% opacity)
- Parchment background for cards
- Clear label hierarchy

### Buttons
- **Primary:** Gold background, black text, uppercase
- **Secondary:** Transparent, gold border, gold text
- **Hover:** Glow effect, slight scale
- **Active:** Gold with shadow depth

---

## Copy & Microcopy

### Page Titles
- "Become the Warrior Your Credit Deserves"
- "Upload Your Battle Plans"
- "Forge Your Dispute Letters"
- "Release Your Authority"
- "Victory Awaits"

### Button Text
- "Begin Your Quest" (CTA)
- "Upload Documents" (Action)
- "Generate Letters" (Action)
- "Release to Bureaus" (Admin)
- "Approve Dispatch" (Admin)
- "Advance to Next Stage" (Navigation)

### Section Headings
- "The Dojo" (Intake)
- "The Koi Pond" (Upload)
- "The Sand Garden" (Review)
- "The Stairway" (Payment)
- "The Dragon Gate" (Confirmation)

### Descriptive Copy
- "Your credit is a battle. We are your armor."
- "Every document strengthens your position."
- "The bureaus will hear from you—clearly, professionally, powerfully."
- "Your victory is earned, not given."

### Error Messages
- "This path requires completion of the previous stage."
- "Your documents were not recognized. Please try again."
- "The bureaus require this information."

### Success Messages
- "Your armor grows stronger."
- "The letters are ready for release."
- "Your authority has been established."

---

## Responsive Design

### Breakpoints
- **Desktop:** 1200px+ (full three-column layout)
- **Tablet:** 768px-1199px (stacked, warrior centered)
- **Mobile:** <768px (vertical stack, warrior full-width)

### Mobile Adjustments
- Left rail moves to top
- Center warrior scales down
- Right panel becomes horizontal scroll
- Typography scales down 10-15%
- Touch targets: 44px minimum

---

## Accessibility

### Color Contrast
- All text: WCAG AA minimum (4.5:1)
- Gold on black: 7.2:1 ✅
- Ivory on black: 12.1:1 ✅

### Focus States
- Gold ring (oklch(0.78 0.13 82))
- 3px width
- Visible on all interactive elements

### Motion
- Respect `prefers-reduced-motion`
- Reduce animation duration by 50% if enabled
- Keep essential transitions

---

## File Structure for Claude Code

```
/design/
├── DESIGN_SPEC.md (this file)
├── colors/
│   └── palette.json
├── typography/
│   └── fonts.css
├── components/
│   ├── hero-section.tsx
│   ├── warrior-stage.tsx
│   ├── path-selector.tsx
│   └── form-section.tsx
├── mockups/
│   ├── landing-page.png
│   ├── dojo-page.png
│   ├── koi-pond-page.png
│   ├── sand-garden-page.png
│   ├── stairway-page.png
│   └── dragon-gate-page.png
├── mascot/
│   ├── mr-beeks-base.svg
│   ├── mr-beeks-armor-1.svg
│   ├── mr-beeks-armor-2.svg
│   ├── mr-beeks-armor-3.svg
│   └── mr-beeks-animations.json
└── copy/
    └── all-copy.md
```

---

## Implementation Notes for Claude Code

1. **Do NOT use generic web templates.** This is a cinematic experience.
2. **Preserve the seascape.** It's the emotional anchor.
3. **Make armor progression visible.** Users need to see their progress.
4. **Use the gold strategically.** It's earned, not decorative.
5. **Respect the typography hierarchy.** Cinzel for ceremony, Rajdhani for clarity.
6. **Animate thoughtfully.** Every motion should serve the narrative.
7. **Test on mobile.** The experience must work on phones.
8. **Get legal review.** CROA compliance is non-negotiable before launch.

---

## Design Decision Log

| Decision | Rationale | Status |
|----------|-----------|--------|
| Cinematic Chanbara Maximalism | Preserves soul while upgrading experience | ✅ Chosen |
| Three-column layout | Asymmetric, not centered; feels intentional | ✅ Approved |
| Gold as primary accent | Represents earned authority, not given | ✅ Approved |
| Warrior as hero | User is the hero, not the form | ✅ Approved |
| Slow animations | Weighty, cinematic, not generic web | ✅ Approved |
| Seascape as origin | Emotional authenticity, user-created | ✅ Approved |

---

**Last Updated:** May 8, 2026  
**Design Lead:** Manus AI  
**Status:** Ready for Claude Code Implementation
