# Mr. Beeks — Mascot Specifications

## Character Overview

**Name:** Mr. Beeks (The Warrior)

**Role:** Central hero of the BitmojiGuy experience. Visual representation of the user's credit repair journey.

**Personality:** Stoic, determined, honorable. A samurai warrior preparing for battle. Starts vulnerable, grows stronger with each stage.

**Visual Style:** Minimalist samurai, inspired by Demon Slayer aesthetic. Clean lines, expressive but restrained. Not cartoonish; dignified and powerful.

---

## Base Design

### Silhouette
- **Height:** 200-300px (responsive scaling)
- **Proportions:** Realistic human figure, standing at attention
- **Stance:** Feet shoulder-width apart, hands at sides or in combat position
- **Head:** Calm, focused expression. Eyes forward.

### Color Palette
- **Skin:** Warm tan (`#C9A876`)
- **Hair:** Black (`#1A1A1A`)
- **Eyes:** Gold accent (`#D4AF37`)
- **Base Clothing:** Dark indigo (`#2C3E50`)

### Base State (No Armor)
- Simple dark tunic
- Bare arms (showing vulnerability)
- Barefoot or in simple sandals
- No weapons or armor
- Slightly transparent (60% opacity) to show "not yet ready"

---

## Armor Progression

Mr. Beeks grows stronger through 5 stages. Each stage adds armor pieces.

### Stage 1: The Dojo (Intake Complete)
**Armor Added:** Arm Guards (Kote)
- Leather arm protection on both forearms
- Gold accents on edges
- Slight glow effect

**Visual Effect:**
- Opacity increases to 80%
- Subtle metallic sheen
- Small spark animation on appearance

### Stage 2: The Koi Pond (Documents Uploaded)
**Armor Added:** Chest Plate (Do)
- Central torso protection
- Layered metal appearance
- Gold rivets and accents

**Visual Effect:**
- Opacity increases to 90%
- Glow intensifies around chest
- Sparks cascade down from shoulders

### Stage 3: The Sand Garden (Disputes Reviewed)
**Armor Added:** Leg Guards (Suneate)
- Shin and thigh protection
- Metal plating with leather straps
- Gold trim

**Visual Effect:**
- Opacity reaches 100%
- Full metallic sheen
- Sparks rise from ground around feet

### Stage 4: The Stairway (Payment Authorized)
**Armor Added:** Helmet (Kabuto)
- Protective headgear with face guard
- Gold crest on top
- Intimidating but honorable

**Visual Effect:**
- Glow effect spreads to entire figure
- Aura of light around character
- Major spark burst

### Stage 5: The Dragon Gate (Disputes Released)
**Armor Added:** Sword (Katana)
- Appears in hand
- Gold-wrapped handle
- Blade catches light

**Visual Effect:**
- Character stands in power pose
- Sword raised or held at ready
- Intense glow and particle effects
- Victory animation (optional)

---

## Animations

### Entrance Animation (600ms)
- Character materializes from top to bottom
- Sparks fall as each section appears
- Slow easing: `cubic-bezier(0.25, 0.46, 0.45, 0.94)`

### Idle Animation (Continuous)
- Subtle breathing motion (±2px vertical)
- Duration: 3 seconds
- Easing: ease-in-out

### Armor Upgrade Animation (800ms)
- Armor piece slides into place from side
- Sparks burst outward
- Metallic "clink" sound (optional)
- Character briefly glows brighter

### Victory Animation (1000ms, on final stage)
- Character raises sword
- Full-body glow
- Particle burst
- Slow motion effect

### Hover Animation (200ms)
- Slight scale increase (1.05x)
- Glow intensifies
- Subtle parallax shift

---

## Technical Specifications

### File Formats
- **Primary:** SVG (scalable, animatable)
- **Fallback:** PNG (48px, 96px, 192px sizes)
- **Animation:** JSON (Lottie format) or CSS keyframes

### SVG Structure
```
<svg viewBox="0 0 200 300" xmlns="http://www.w3.org/2000/svg">
  <!-- Base Layer -->
  <g id="base">
    <ellipse id="head" />
    <path id="body" />
    <path id="legs" />
    <path id="feet" />
  </g>

  <!-- Armor Layers (hidden by default) -->
  <g id="armor-stage-1" style="display: none;">
    <path id="arm-guards" />
  </g>
  <g id="armor-stage-2" style="display: none;">
    <path id="chest-plate" />
  </g>
  <!-- ... etc ... -->

  <!-- Effects -->
  <g id="effects">
    <defs>
      <filter id="glow">
        <feGaussianBlur stdDeviation="3" result="coloredBlur" />
      </filter>
    </defs>
    <circle id="glow-ring" filter="url(#glow)" />
  </g>
</svg>
```

### CSS Animations
```css
@keyframes armor-upgrade {
  0% {
    transform: translateX(-20px);
    opacity: 0;
  }
  50% {
    filter: drop-shadow(0 0 10px #D4AF37);
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes idle-breathe {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}

@keyframes spark-burst {
  0% {
    opacity: 1;
    transform: translate(0, 0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(var(--tx), var(--ty)) scale(0);
  }
}
```

### Responsive Scaling
- **Desktop (1200px+):** 300px height
- **Tablet (768px-1199px):** 250px height
- **Mobile (<768px):** 200px height

---

## Color Variations

### Default (Dark Mode)
- Skin: `#C9A876`
- Hair: `#1A1A1A`
- Eyes: `#D4AF37`
- Armor: `#3A3A3A` with gold accents

### Light Mode (If Needed)
- Skin: `#D4A574`
- Hair: `#2C2C2C`
- Eyes: `#B8860B`
- Armor: `#5A5A5A` with gold accents

### Accessibility (High Contrast)
- Skin: `#E8C9A0`
- Hair: `#000000`
- Eyes: `#FFD700`
- Armor: `#FFFFFF` with black outlines

---

## Particle Effects

### Sparks
- **Color:** Gold (`#D4AF37`)
- **Size:** 2-4px circles
- **Duration:** 600-800ms
- **Count:** 8-12 per burst
- **Spread:** Radial, 360 degrees
- **Easing:** ease-out

### Glow Aura
- **Color:** Gold with transparency
- **Blur:** 10-20px
- **Opacity:** 0.3-0.6
- **Pulse:** 2-3 second cycle
- **Trigger:** On armor upgrade or hover

### Metallic Highlights
- **Color:** White with 30% opacity
- **Position:** On armor edges
- **Movement:** Subtle shimmer
- **Duration:** Continuous

---

## Integration Points

### React Component
```tsx
<MrBeeks 
  stage={currentStage}  // 0-5
  isHovered={isHovered}
  isAnimating={isAnimating}
  size="large"  // small, medium, large
/>
```

### CSS Classes
```css
.mr-beeks {
  /* Base styles */
}

.mr-beeks.stage-1 #armor-stage-1 {
  display: block;
}

.mr-beeks.stage-2 #armor-stage-2 {
  display: block;
}

/* ... etc ... */

.mr-beeks:hover {
  animation: hover-glow 0.2s ease-out;
}

.mr-beeks.upgrading {
  animation: armor-upgrade 0.8s ease-out;
}
```

---

## Sound Design (Optional)

### Armor Upgrade Sound
- **Type:** Metallic "clink" or "whoosh"
- **Duration:** 200-300ms
- **Volume:** Medium (not jarring)
- **Trigger:** On armor appearance

### Victory Sound
- **Type:** Triumphant orchestral swell
- **Duration:** 1-2 seconds
- **Volume:** Prominent
- **Trigger:** On final stage completion

---

## Design Principles

1. **Dignity Over Cuteness:** Mr. Beeks is honorable, not cute. Respect the user's journey.
2. **Minimalist Details:** Clean lines. Every element serves a purpose.
3. **Gold Accents:** Gold represents earned authority. Use it strategically.
4. **Progression Visibility:** Each armor piece should be clearly visible and distinct.
5. **Cinematic Motion:** Animations should feel weighty and intentional.
6. **Accessibility:** High contrast, clear shapes, no flashing effects.

---

## File Deliverables

- `mr-beeks-base.svg` — Base character without armor
- `mr-beeks-armor-1.svg` — Arm guards
- `mr-beeks-armor-2.svg` — Chest plate
- `mr-beeks-armor-3.svg` — Leg guards
- `mr-beeks-armor-4.svg` — Helmet
- `mr-beeks-armor-5.svg` — Sword
- `mr-beeks-animations.json` — Lottie animation data
- `mr-beeks-component.tsx` — React component
- `mr-beeks-styles.css` — All CSS animations and styles

---

**Last Updated:** May 8, 2026  
**Status:** Ready for Design Implementation  
**Next Step:** Create SVG files based on specifications above
