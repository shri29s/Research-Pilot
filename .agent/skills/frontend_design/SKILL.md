---
name: premium-frontend-design
description: >
  Use this skill when building any UI that needs to feel premium, editorial,
  or craft-level — landing pages, dashboards, portfolios, SaaS marketing sites,
  or any interface where the visual quality bar is "could be mistaken for a
  top-tier design studio's work." Covers React, Vue, vanilla HTML/CSS/JS.
  Includes SVG illustration, motion design, and typographic craft patterns.
  Triggers on: "premium design", "elegant UI", "not AI slop", "Framer-style",
  "high-end", "boutique feel", "top-tier landing page", "award-worthy", or
  any brief where the person has explicitly rejected generic output.
---

# Premium Frontend Design Skill

You are the lead creative at a studio that consistently ships work that wins
awwwards, gets featured in Lapa Ninja, and makes people ask "what framework
is this?" — even when the answer is "just HTML and CSS." This skill tells you
exactly how to replicate that quality floor.

---

## 1. The mindset shift

Generic AI output looks the same because it solves the wrong problem first.
It asks "what components do I need?" You should ask:

> "What is the *one image* someone should carry away from this page, and what
> is the most unexpected form it could take?"

Everything else — layout, color, type, motion — exists to deliver that image.
Start there, not with a nav bar and a hero CTA.

---

## 2. Token system: build this before writing a single element

### Color — fewer, harder

Pick 2 anchor colors maximum, then derive everything else via opacity and mix.
Never use `#ffffff` or `#000000` as your surface or text — add a tiny tint
(warm, cool, or tinted dark). Name every color by role, not by value.

```
--color-surface:      #0B0C0F   /* near-black with cool blue tint */
--color-surface-mid:  #13151A   /* card/panel layer */
--color-surface-hi:   #1E2029   /* elevated element */
--color-accent:       #C8FF00   /* single acid-lime signal */
--color-accent-dim:   rgba(200,255,0,0.12) /* ambient glow / tint */
--color-text-primary: #F0EFE8   /* warm off-white */
--color-text-secondary: #7A7F8A
--color-rule:         rgba(255,255,255,0.08)
```

**Rules:**
- One accent, used sparingly (border, underline, icon fill, hover state)
- Surface layers differ by lightness only, never hue-jump between layers
- Never use a color you did not name in the token system

### Type — two faces, used with purpose

Pair a **display face** (expressive, used at 64px+, never body copy) with a
**utility face** (neutral, optical-size aware, 13–18px range).

Good pairings for premium work:
| Display | Utility | Mood |
|---------|---------|------|
| PP Editorial New | Inter | Editorial dark |
| Canela | Söhne | Luxury warm |
| Neue Haas Display | DM Mono | Technical cold |
| Italiana | Plus Jakarta Sans | Fashion |

Use Google Fonts or Bunny Fonts for web-safe delivery. Never use the same
family in display and body. Set `font-feature-settings: "ss01", "cv01"` for
optical refinement where available.

```css
--font-display: 'PP Editorial New', 'Playfair Display', Georgia, serif;
--font-body:    'Inter', system-ui, sans-serif;
--font-mono:    'DM Mono', 'Fira Code', monospace;

--size-display-xl:  clamp(64px, 8vw, 120px);
--size-display-lg:  clamp(40px, 5vw, 72px);
--size-heading:     clamp(24px, 3vw, 40px);
--size-body:        16px;
--size-caption:     13px;

--leading-display:  0.95;    /* tight, editorial */
--leading-body:     1.65;    /* open, readable  */
--tracking-display: -0.03em;
--tracking-caption: 0.12em;  /* uppercase labels: always tracked out */
```

### Spacing — 8pt grid, with intentional breaks

Base: 8px. Scale: 4, 8, 16, 24, 32, 48, 64, 96, 128, 192. Never use odd
numbers (e.g. 15px, 23px) unless compensating for optical illusion. Section
breathing room should be ≥ 128px top/bottom on desktop.

### Motion — one curve, used consistently

```css
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out-circ: cubic-bezier(0.85, 0, 0.15, 1);
--duration-fast: 180ms;
--duration-base: 320ms;
--duration-slow: 600ms;
```

Animate: opacity + transform together. Never animate `width`, `height`,
`top`, `left` — use `transform: scaleX()` and `translate()`.

---

## 3. SVG as design material

SVG is where premium UI separates from template UI. Use it for:

### Organic geometry — noise-displaced shapes
```svg
<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="noise">
      <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3"
                    stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
      <feBlend in="SourceGraphic" mode="overlay"/>
    </filter>
    <radialGradient id="blob" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="var(--color-accent)" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="var(--color-accent)" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <ellipse cx="300" cy="300" rx="220" ry="200" fill="url(#blob)"
           filter="url(#noise)" transform="rotate(-20 300 300)"/>
</svg>
```

### Grid / mesh patterns (structural texture)
```svg
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none"
        stroke="rgba(255,255,255,0.06)" stroke-width="0.5"/>
</pattern>
<rect width="100%" height="100%" fill="url(#grid)"/>
```

### Animated gradient borders
```css
.card-premium {
  border: 1px solid transparent;
  background:
    linear-gradient(var(--color-surface-mid), var(--color-surface-mid))
    padding-box,
    linear-gradient(135deg, var(--color-accent), transparent 60%)
    border-box;
}
```

### Clip-path reveals (scroll-triggered)
```css
.reveal {
  clip-path: inset(0 100% 0 0);
  transition: clip-path 0.8s var(--ease-out-expo);
}
.reveal.in-view {
  clip-path: inset(0 0% 0 0);
}
```

### Morphing blobs (ambient atmosphere)
Use `<animateTransform>` or CSS `@keyframes` with SVG paths. Keep subtle —
think 20s loop, low-opacity. This is atmosphere, not a feature.

---

## 4. Layout patterns worth using

### Full-bleed hero with typographic anchor
The headline breaks the grid intentionally — one word or phrase at maximum
size, optionally outlined (`-webkit-text-stroke`) vs filled, creating figure/
ground contrast within the type itself.

### Staggered card grid (not uniform)
Vary column widths: `grid-template-columns: 3fr 2fr` or use `grid-template-areas`
to let feature cards span. Never 3-equal-column card grids unless the content
is truly undifferentiated.

### Sticky horizontal scroll section
Let one section scroll horizontally while the page stays put — great for
showcasing features, work samples, or timeline. Use `position: sticky` +
`transform: translateX()` driven by scroll progress.

### Split-screen with live/animated side
One column: static editorial type and label stack. Other column: animated
SVG, canvas, or CSS experiment. The contrast between stillness and motion is
the composition.

### Table as design element
Monospaced, bordered tables with alternating row tints and a hover state that
reveals a hidden column. Turns data into furniture.

---

## 5. Framework-specific patterns

### React
```jsx
// Motion-driven component with intersection observer
import { useEffect, useRef, useState } from 'react'

const FadeIn = ({ children, delay = 0 }) => {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setVisible(true); obs.disconnect() }
    }, { threshold: 0.15 })
    obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])

  return (
    <div ref={ref} style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'none' : 'translateY(24px)',
      transition: `opacity 0.6s ${delay}ms var(--ease-out-expo),
                   transform 0.6s ${delay}ms var(--ease-out-expo)`
    }}>
      {children}
    </div>
  )
}
```

### Vue
```vue
<script setup>
import { ref, onMounted } from 'vue'

const visible = ref(false)
const el = ref(null)

onMounted(() => {
  const obs = new IntersectionObserver(([e]) => {
    if (e.isIntersecting) { visible.value = true; obs.disconnect() }
  }, { threshold: 0.15 })
  obs.observe(el.value)
})
</script>

<template>
  <div ref="el" :class="['reveal', { 'in-view': visible }]">
    <slot />
  </div>
</template>
```

### Vanilla / Alpine.js
Use `x-intersect` (Alpine) or a lightweight `IntersectionObserver` wrapper.
Keep JS under 50 lines; prefer CSS doing the heavy lifting.

### Tailwind augmentation
Tailwind covers spacing and layout well but its defaults read as generic.
Override with CSS variables for color and type. Use `@apply` sparingly —
prefer semantic class names for components that carry design intent.

---

## 6. What never to do (anti-patterns)

| Do this | Not this |
|---------|----------|
| `color: var(--color-text-secondary)` | `color: #6b7280` (Tailwind gray) |
| A deliberate display face, 96px | `font-size: 3rem; font-weight: 700` system font |
| One accent color, used in 3 places max | Gradient rainbow across CTAs |
| SVG ambient element or noise texture | A stock photo hero with overlay |
| `border-radius: 2px` or `0` for dark tech | `border-radius: 12px` on everything |
| Custom hover state aligned to the design | `opacity: 0.7` on hover |
| Motion along a single axis | Zoom + spin + fade simultaneously |
| Whitespace doing compositional work | Padding-filled empty space |
| Real copy written for this design | "Lorem ipsum" or "Discover. Build. Scale." |
| A grid break as a deliberate moment | Perfect symmetry everywhere |

---

## 7. Quality checklist before shipping

- [ ] Does the page have one unmistakable signature element?
- [ ] Could the type pairing appear on any other project, or is it specific?
- [ ] Does every SVG element earn its place (texture, structure, illustration)?
- [ ] Is motion serving clarity, or just performing?
- [ ] Are shadows coherent (one light source, consistent blur/spread)?
- [ ] Does the design hold at 375px mobile?
- [ ] `prefers-reduced-motion` respected with `@media` query?
- [ ] Is any color used that wasn't in the token system?
- [ ] Does the copy sound like a person wrote it for this specific product?
- [ ] Is there one element you'd cut if forced to? Cut it.

---

## 8. Reference designs included

See `references/` folder:

- **design-1-saas-dashboard.html** — Dark premium SaaS landing page. Features:
  animated SVG blob atmosphere, gradient border cards, custom display type,
  staggered grid, and an SVG noise-texture hero.

- **design-2-portfolio.html** — Light editorial portfolio / agency site. Features:
  split-screen layout, outline type treatment, horizontal scroll showcase
  section, and a morphing SVG mark as the logo.

Study the token systems and component patterns in these files as templates.
When generating new designs, copy the token scaffolding and swap the palette,
type pair, and signature element to fit the new brief.

---

## 9. Phrase the brief back before building

Before writing code, state in one sentence:
> "This is a [type of product] for [audience], and the one image I want them
> to leave with is [specific image], delivered via [design approach]."

If you can't fill in that sentence with specifics, ask the person one question
to unlock it. Don't build until you can fill it in.