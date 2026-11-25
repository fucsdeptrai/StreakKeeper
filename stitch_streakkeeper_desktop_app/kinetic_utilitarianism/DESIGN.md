---
name: Kinetic Utilitarianism
colors:
  surface: '#10141a'
  surface-dim: '#10141a'
  surface-bright: '#353940'
  surface-container-lowest: '#0a0e14'
  surface-container-low: '#181c22'
  surface-container: '#1c2026'
  surface-container-high: '#262a31'
  surface-container-highest: '#31353c'
  on-surface: '#dfe2eb'
  on-surface-variant: '#e1bfb5'
  inverse-surface: '#dfe2eb'
  inverse-on-surface: '#2d3137'
  outline: '#a98a80'
  outline-variant: '#594139'
  surface-tint: '#ffb59d'
  primary: '#ffb59d'
  on-primary: '#5d1900'
  primary-container: '#ff6b35'
  on-primary-container: '#5f1900'
  inverse-primary: '#ab3500'
  secondary: '#67df70'
  on-secondary: '#00390d'
  secondary-container: '#27a640'
  on-secondary-container: '#00320a'
  tertiary: '#ffb689'
  on-tertiary: '#512300'
  tertiary-container: '#e57f36'
  on-tertiary-container: '#532400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdbd0'
  primary-fixed-dim: '#ffb59d'
  on-primary-fixed: '#390c00'
  on-primary-fixed-variant: '#832600'
  secondary-fixed: '#83fc89'
  secondary-fixed-dim: '#67df70'
  on-secondary-fixed: '#002105'
  on-secondary-fixed-variant: '#005317'
  tertiary-fixed: '#ffdbc8'
  tertiary-fixed-dim: '#ffb689'
  on-tertiary-fixed: '#311300'
  on-tertiary-fixed-variant: '#743500'
  background: '#10141a'
  on-background: '#dfe2eb'
  surface-variant: '#31353c'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  label-code:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-badge:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.01em
  label-kbd:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-compact: 0.5rem
  margin: 1rem
  margin-window: 1.25rem
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

The design system embodies precision productivity, crafted specifically for power users, developers, and habit-driven professionals who demand speed, dense information architecture, and tactile digital mechanics. Drawing directly from modern desktop power-tools such as Raycast and Linear, the aesthetic fuses minimalist brutalist discipline with sophisticated dark-mode ergonomics.

### Personality & Values
- **Hyper-focused & Zero-Latency Feel:** UI chrome recedes completely, letting data density, streak metrics, and keyboard workflows dominate.
- **Instrument-grade Precision:** Pixel-sharp outlines, micro-type scales, and monospaced indicators treat everyday habit tracking with the gravitas of developer tooling.
- **Tactile Feedback:** Accent glows and crisp state transitions simulate hardware keycaps and terminal dashboards.

### Aesthetic Movement
Modern Utilitarian Dark Mode: High-density layouts, subtle background gradations, low-contrast 1px hairline separation, monospaced metadata, and selective warm flame accents that signal kinetic momentum without causing visual fatigue.

## Colors

The palette utilizes deeply subdued GitHub/Linear-inspired dark slate neutrals punctuated by an energetic flame-orange core. This ensures that long operational sessions remain low-strain while streaks, hotkeys, and actionable items stand out with absolute clarity.

### Functional Palette
- **Canvas Base (`#0D1117`):** Primary desktop window surface.
- **Surface Elevation 1 (`#161B22`):** Sidebar panels, command bars, grouped lists.
- **Surface Elevation 2 (`#21262D`):** Hover states, active row selections, floating modal sheets.
- **Hairline Border (`#30363D`):** Crisp structural dividers and component edges.
- **Primary / Kinetic Orange (`#FF6B35` / hover `#FF5722`):** Core streak markers, active toggles, primary execution buttons, and flame icons.
- **Success / Maintained Streak (`#238636` base, `#3FB950` text/indicator):** Completed streaks, verified actions.
- **Warning / At-Risk Amber (`#D29922` base, `#F0883E` bright):** Habits nearing daily expiration, pending verifications.
- **Destructive / Broken Streak (`#F85149`):** Reset warnings, dropped streaks, critical deletions.

### Text Contrast Hierarchy
- **Text High-Contrast:** `#F0F6FC` (Headings, active values, focused items)
- **Text Standard:** `#C9D1D9` (Body content, habit names, list titles)
- **Text Muted:** `#8B949E` (Metadata, timestamps, hotkey labels)
- **Text Subtle / Disabled:** `#484F58` (Dividers, inactive status glyphs)

## Typography

Typography prioritizes high-density scannability and terminal-adjacent technical authority. `Inter` provides neutral, perfectly balanced letterforms across body copy and titles, while `JetBrains Mono` grounds metrics, day-counts, streak tallies, and keyboard shortcut glyphs.

- Tight negative letter-spacing on display headings delivers an authoritative, engineered character.
- Text sizes remain compact (11px–14px standard) to preserve visual room for multi-column grids, heatmaps, and command palette overlays.
- Numbers, metrics, and shortcuts always render with tabular numbers (`font-feature-settings: 'tnum' 1`) to eliminate jitter during active counts.

## Layout & Spacing

The design system is calibrated around a disciplined desktop window container standard (aspect ratio optimized for 1000×680 and expandable fluid workspaces). 

### Layout Model
- **Dual-Pane Utility Division:** 240px fixed navigation sidebar alongside a flexible master detail / multi-pane habit matrix.
- **Top Utility Rail (36px height):** Integrated window drag area, quick search trigger (`⌘K`), and streak fire counter.
- **Data Matrix:** Habits render in high-density horizontal rows with fixed 40px row heights and 8px inline spacing between cell indicators.

### Breakpoints & Adaptability
- **Desktop Windowed (1000px × 680px standard):** Full 2-column layout + right contextual inspection drawer.
- **Compact Floating Widget (380px – 520px):** Sidebar collapses into an icon ribbon; habit rows convert into single-line tickable list items with condensed shortcut hints.
- **Expanded Ultrawide / Multi-Window (>1280px):** Spans habit calendar heatmaps, velocity charts, and daily log sidebars into a 3-column command dashboard.

## Elevation & Depth

Visual hierarchy is maintained via tonal layering combined with hairline borders rather than muddy, diffusive shadows. This yields an airtight, low-profile look common in modern developer runtimes.

- **Base Layer:** `#0D1117` provides total background canvas isolation.
- **Layer 1 (Containers, Sidebars, Field Backgrounds):** `#161B22` framed by a 1px solid border of `#30363D`.
- **Layer 2 (Hover Highlights, Selected Rows, Dropdown Menus):** `#21262D` surface tint with `#30363D` borders.
- **Floating Modals & Command Palettes:** `#161B22` with a 24px backdrop blur (`backdrop-filter: blur(16px) saturate(180%)`), supported by a 1px solid `#484F58` accent outline and an ambient shadow: `0 16px 40px -8px rgba(0, 0, 0, 0.65), 0 0 1px 1px rgba(255, 107, 53, 0.15)`.
- **Active Hotkey & Focal Glow:** Focused controls receive a crisp 1px ring in `#FF6B35` with an ultra-soft 4px outer blur (`box-shadow: 0 0 0 1px #FF6B35, 0 0 8px rgba(255, 107, 53, 0.25)`).

## Shapes

The design system adopts a disciplined "Soft" curvature philosophy (`roundedness: 1`). Controls exhibit structural 4px (`0.25rem`) corner radiuses, maintaining crisp architectural precision while avoiding aggressive brutalist edge harshness.

- **Base Controls (Buttons, Inputs, Row Selectors, Badges):** 4px border radius (`0.25rem`).
- **Cards, Popovers, and Dialog Frames (`rounded-lg`):** 8px border radius (`0.5rem`).
- **Window Outer Chrome (`rounded-xl`):** 12px border radius (`0.75rem`) to match macOS/Windows 11 desktop window frames.
- **Streak Activity Blocks (Heatmap squares):** 2px corner radius for dense, high-frequency daily activity grids.
- **Keyboard Badges (`kbd`):** 3px border radius with a solid bottom border lip to simulate mechanical micro-keys.

## Components

### Buttons & Interactive Triggers
- **Primary Kinetic Action:** Background `#FF6B35`, text `#FFFFFF`, 4px radius, font size 12px/weight 600. On hover, background shifts to `#FF5722`.
- **Secondary / Ghost Button:** Background `#21262D`, 1px border `#30363D`, text `#C9D1D9`. On hover, border shifts to `#8B949E` and text to `#F0F6FC`.
- **Keyboard Shortcut Hints (`kbd`):** Nestled at the trailing edge of buttons and dropdown items. Surface `#161B22`, border `#30363D`, text `#8B949E`, padding `1px 4px`, font `JetBrains Mono` 10px.

### Streak Chips & Status Indicators
- **Active Flame Pill:** Background `rgba(255, 107, 53, 0.12)`, border `1px solid rgba(255, 107, 53, 0.35)`, text `#FF6B35`. Features flame icon prefix with numeric streak counter in tabular numbers.
- **Completed Today:** Background `rgba(35, 134, 54, 0.15)`, border `1px solid rgba(63, 185, 80, 0.35)`, text `#3FB950`.
- **At-Risk Pill:** Background `rgba(210, 153, 34, 0.12)`, border `1px solid rgba(240, 136, 62, 0.35)`, text `#F0883E`.

### Habit List Rows
- Height 40px, inline padding 8px, border-bottom 1px solid `#21262D`.
- Hover state transitions instantly to `#161B22` with a 2px left border accent in `#FF6B35`.
- Contains: Drag handle, habit icon, title, streak counter chip, 7-day mini dot history, and completion checkbox.

### Selection Controls (Checkboxes & Radios)
- **Streak Checkbox:** 16×16px box, 1px border `#484F58`, radius 3px, background `#161B22`.
- **Checked State:** Instant transition to `#238636` background with a bright `#3FB950` check icon, or flame-orange `#FF6B35` on milestone streaks.

### Input Fields & Command Palettes
- **Command Search Input (`⌘K` bar):** Unbordered or subtle 1px border `#30363D`, 36px height, font size 13px, background `#161B22`. Placeholder text in `#8B949E`. Focus state utilizes `#FF6B35` hairline accent with zero displacement.

### Calendar Heatmap & Velocity Grid
- Monospaced grid of 10×10px blocks with 2px gaps.
- Scale: Level 0 (`#161B22`), Level 1 (`#3E2015`), Level 2 (`#7A3517`), Level 3 (`#C44F1F`), Level 4 (`#FF6B35`).