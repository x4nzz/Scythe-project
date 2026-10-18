# Scyth Dashboard Overhaul — Design Spec

## 1. Intent

Completely rebuild the Scyth Discord bot web dashboard into a premium dark-mode landing page inspired by bleed.bot's structure and hierarchy, with a custom monochrome Scyth/Reaper theme. Deployable on bot-hosting.net alongside `main.py` without breaking startup or env-var configuration.

## 2. Constraints

- **Palette**: pure black `#000000`, dark greys `#0a0a0a` `#111111` `#1a1a1a`, white `#ffffff`, metallic silver `#c0c0c0` / `#a0a0a0`.
- **No**: neon colors, purple, blue accents, gradient text, emojis in headings, glassmorphism, colored left-border cards, badges above headline, unfocused scroll-fade animations, cursor-tracking beams.
- **Tech stack**: Next.js 16 App Router (existing), Tailwind CSS v4 (existing), Framer Motion (new dependency), Lucide icons (new dependency, used sparingly).
- **Deployment**: `main.py` launches dashboard via `npm run dev` in `/dashboard` with `HOST`/`PORT` env vars. Must not break.
- **Keep**: existing routing, existing startup, env var setup.

## 3. Architecture

### 3.1 Files to create / modify

| Path | Action | Purpose |
|------|--------|---------|
| `dashboard/package.json` | modify | Add `framer-motion`, `lucide-react` deps |
| `dashboard/tailwind.config.js` | rewrite | Add custom animations, blade slash keyframes, grid pattern |
| `dashboard/src/app/globals.css` | rewrite | Base styles, font (Orbitron for headings, monospace body), grid bg |
| `dashboard/src/app/layout.tsx` | modify | Wire Framer Motion `MotionConfig`, add `<html>` attrs |
| `dashboard/src/app/page.tsx` | rewrite | Re-export hero → features → command browser in order |
| `dashboard/src/components/Hero.tsx` | rewrite | Slasher title, tagline, CTA buttons, live stats |
| `dashboard/src/components/BladeSlash.tsx` | create | Reusable diagonal blade slash animation component |
| `dashboard/src/components/FeatureGrid.tsx` | rewrite | Feature cards with sharp hover + slash |
| `dashboard/src/components/CommandBrowser.tsx` | rewrite | Search, category tabs, command list from `COMMAND_SYNTAX` |
| `dashboard/src/lib/commands.ts` | create | Static command data extracted from `main.py` `COMMAND_SYNTAX` |
| `dashboard/src/components/NowPlaying.tsx` | create | "Listening to" card (preserved from old design per instructions) |
| `dashboard/src/components/ui/StatCard.tsx` | create | Reusable stat card for hero live stats |
| `dashboard/public/scyth-logo.svg` | create | Custom Scyth logo / scythe icon |
| `dashboard/src/app/commands/page.tsx` | create | `/commands` route (linked from Hero "Commands" button) |

### 3.2 Data flow

```
main.py (bot)
  └── npm run dev (dashboard)
        ├── /app/(page.tsx)          ← Hero, FeatureGrid, CommandBrowser, NowPlaying
        ├── /app/commands/(page.tsx) ← Full command browser
        ├── /app/layout.tsx          ← RootLayout + MotionConfig
        └── /lib/commands.ts         ← Static command definitions
```

Commands data: The dashboard will ship a static `commands.ts` file mirroring `COMMAND_SYNTAX` from `main.py`. This avoids a live API dependency and works in static export if needed. The bot updates `COMMAND_SYNTAX` infrequently.

### 3.3 Styling approach

- **Font**: `Orbitron` (Google Fonts, loaded via `<link>` in layout) for headings — sharp, angular, fits "scythe" aesthetic. Body text: system monospace stack.
- **Grid background**: Subtle CSS grid pattern at 20px intervals, opacity ~0.03, only visible in dark.
- **Blade slash**: Framer Motion `<motion.div>` with absolute positioning, diagonal white gradient (0.5px wide), animated translateX across container on mount and hover.
- **Sharp borders**: `border-[1px]` with `border-white/5`, `shadow-[0_0_20px_rgba(255,255,255,0.02)]` for subtle glow.
- **No glassmorphism**: `backdrop-blur` avoided. Cards use solid `#111111` / `#1a1a1a` backgrounds.

## 4. Section Designs

### Hero Section

**Background**: Pure black, subtle grid pattern overlay.

**Blade slash animation**: A 0.5px diagonal white gradient line sweeps across the hero on mount (Framer Motion). On mouse hover over the title area, a secondary slash triggers.

**Title**: "SCYTH" in Orbitron Bold, 5xl+ on desktop, tracking-tighter. Each letter wrapped or the entire word animated with a blade-draw effect (staggered letter reveals + slash through center).

**Tagline**: "Moderation • Music • Utilities" — same as existing but restyled in monospace, `#a0a0a0`.

**Buttons**:
1. "Add to Discord" — solid `#ffffff` text on `#000000` background border, sharp corners, no rounded. Hover: subtle silver glow.
2. "Commands" — outlined with `#c0c0c0` border, transparent bg, white text. Hover: fills with `#111111` bg.

**Live stats bar**: 4 cards in a row (grid on mobile):
- Servers — `#ffffff` number, `#a0a0a0` label
- Users — same
- Commands Used — same
- Uptime — same (e.g. "99.9%")

Each card: `#0a0a0a` background, sharp border `#1a1a1a`, `py-3 px-5`, centered text. Hover: blade slash overlay + silver border glow.

### Feature Grid

5 cards in responsive grid (1 col mobile, 2 col tablet, 3 col desktop):

1. **Moderation** — ShieldCheck icon
2. **Music** — Music icon
3. **Utility** — Terminal icon
4. **Auto-Mod** — Bot icon (anti-raid/nuke automation)
5. **Custom Commands** — Command icon

Each card: `#111111` background, `#1a1a1a` border, sharp edges (`rounded-none`). Icon in `#c0c0c0`. Hover: blade slash sweeps diagonally across, border glows silver.

Icons: Minimal Lucide icons, 1px stroke, `#a0a0a0`. Used sparingly — only in feature grid.

### Command Browser

**Search bar**: Full width, `#0a0a0a` bg, `#1a1a1a` border, sharp corners, white text placeholder `#555`. Focus ring: 1px solid silver.

**Category tabs**: Admin, Fun, Music, Config (matching `main.py` help categories). Tab style: `#111` bg, `#1a1a1a` border, inactive hover fills `#0a0a0a`. Active: silver border + `#111111` bg.

**Command list**: Each item is a sharp card:
- Left: command name `;ban` in silver monospace
- Center: description in white
- Right: category tag as small text

Hover: blade slash + border silver glow. No fade-in scroll animations.

### NowPlaying Card (Listening to)

Per instructions: "Keep existing 'Listening to' card exactly as it is if it already exists." It does not exist yet in the dashboard components, but the bot stores `active_playback` in SQLite. Create a minimal card showing the current track (title, artist, duration) pulled from a placeholder. On hover: blade slash animation.

## 5. Color tokens (Tailwind extend)

```
colors: {
  black:     '#000000',
  'dark-1':  '#0a0a0a',
  'dark-2':  '#111111',
  'dark-3':  '#1a1a1a',
  white:     '#ffffff',
  silver:    '#c0c0c0',
  'dark-silver': '#a0a0a0',
}
```

## 6. Framer Motion patterns

| Element | Animation |
|---------|-----------|
| Hero title "SCYTH" | Stagger children: each letter slides + fades from bottom. Blade slash sweeps once on mount. |
| Blade slash (general) | `motion.div` with `background: linear-gradient(135deg, transparent 48%, rgba(255,255,255,0.12) 50%, transparent 52%)`, animate `x` from `-100%` to `100%`, duration 0.6, ease "tween". |
| Stat cards | Mount: scale 0.95 → 1, opacity 0 → 1. Hover: slash + border glow. |
| Feature cards | Hover: slash + translateY(-2px). Border color `#c0c0c0`. |
| Command list items | No scroll fade. Entry: opacity 0 → 1 staggered. Hover: slash. |

## 7. Deployment compatibility

- `main.py` line ~1262: `subprocess_exec("npm", "run", "dev", cwd=dashboard/, env={HOST, PORT})` — unchanged.
- Dashboard must work with `next dev` (dev mode) on bot-hosting.net.
- No static export needed; bot-hosting.net restarts the bot which restarts `npm run dev`.
- `package.json` scripts (`dev`, `build`, `start`, `lint`) unchanged, just new deps.
- No new env vars on the Python side. Dashboard can read `NEXT_PUBLIC_` prefixed vars if needed later, but for now all data is static.

## 8. Out of scope

- Server-side Discord API integration (OAuth, guild data). Dashboard is a static marketing/command-browser landing page. Future: connect to bot's HTTP API for live stats.
- shadcn/ui components (explicitly avoided).
- Any colored accents beyond the monochrome palette.
