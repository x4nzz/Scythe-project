# Scyth Dashboard Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Scyth Discord bot web dashboard with a premium dark monochrome theme, blade slash animations, and three main sections (Hero, Feature Grid, Command Browser) using Next.js 16, Tailwind CSS v4, Framer Motion, and Lucide icons.

**Architecture:** Replace existing dashboard components with new ones matching the design spec. Add Framer Motion and Lucide React as dependencies. Create static command data from main.py's COMMAND_SYNTAX. Preserve existing Next.js startup via main.py (npm run dev).

**Tech Stack:** Next.js 16.4.2 App Router, React 19, Tailwind CSS v4, Framer Motion 12+, Lucide React, TypeScript.

**Spec:** docs/superpowers/specs/2026-10-18-scyth-dashboard-overhaul-design.md

## Global Constraints

- Palette ONLY: `#000000`, `#0a0a0a`, `#111111`, `#1a1a1a`, `#ffffff`, `#c0c0c0`, `#a0a0a0`
- NO neon, purple, blue, gradient text, emojis in headings, glassmorphism, colored left borders, badges above headline, cursor beams, scroll-fade animations
- Font: Orbitron for headings (Google Fonts), system monospace for body
- Framer Motion for all animations (blade slash, hover, mount)
- Deployable on bot-hosting.net: main.py launches `npm run dev` in /dashboard with HOST/PORT env vars — must not break
- Keep existing routing and startup

## Review Focus

1. **Blade slash animation performance** — 60fps on low-end devices, no layout shift
2. **Color palette enforcement** — no accidental color leaks (e.g., focus rings, defaults)
3. **Mobile responsiveness** — hero stats stack, feature grid collapses, command browser scrolls
4. **Accessibility** — focus states visible, semantic HTML, motion respects prefers-reduced-motion
5. **Deployment compatibility** — `npm run dev` starts without errors on bot-hosting.net Node version

---

### Task 1: Add Dependencies & Update package.json

**Files:**
- Modify: `dashboard/package.json`

**Interfaces:**
- Produces: `framer-motion` and `lucide-react` available for import

- [ ] **Step 1: Write the failing test**
```bash
# Test: dependencies install and types resolve
cd dashboard && npm install framer-motion lucide-react --legacy-peer-deps
```

- [ ] **Step 2: Run test to verify it fails** (before install)
Run: `cd dashboard && npm ls framer-motion lucide-react 2>/dev/null || echo "MISSING"`
Expected: MISSING

- [ ] **Step 3: Update `dashboard/package.json`** — add to dependencies:
```json
"framer-motion": "^12.0.0",
"lucide-react": "^0.400.0"
```

- [ ] **Step 4: Install and verify**
Run: `cd dashboard && npm install --legacy-peer-deps && npm ls framer-motion lucide-react`
Expected: Both packages listed with versions

- [ ] **Step 5: Commit**
```bash
git add dashboard/package.json dashboard/package-lock.json
git commit -m "deps: add framer-motion and lucide-react"
```

---

### Task 2: Rewrite Tailwind Config with Animations & Blade Slash Keyframes

**Files:**
- Modify: `dashboard/tailwind.config.js`

**Interfaces:**
- Produces: Tailwind color tokens, `animate-blade-slash`, grid pattern utilities

- [ ] **Step 1: Write the failing test**
```bash
# Test: config compiles and colors resolve
cd dashboard && npx tailwindcss --help 2>/dev/null && echo "OK" || echo "FAIL"
```

- [ ] **Step 2: Run test to verify it fails** (current config is minimal)
Run: `cd dashboard && grep -c "blade-slash" tailwind.config.js || echo "0"`
Expected: 0

- [ ] **Step 3: Rewrite `dashboard/tailwind.config.js`** with:
- Extended colors from spec (black, dark-1/2/3, white, silver, dark-silver)
- Custom keyframes: `blade-slash` (translateX -100% to 100%)
- Animation: `animate-blade-slash` (0.6s ease-out)
- Grid pattern utility class: `bg-grid-pattern`

- [ ] **Step 4: Verify config compiles**
Run: `cd dashboard && npx tailwindcss -o /dev/null 2>&1 | head -5`
Expected: No errors

- [ ] **Step 5: Commit**
```bash
git add dashboard/tailwind.config.js
git commit -m "config: add blade slash animations and monochrome palette"
```

---

### Task 3: Rewrite globals.css with Base Styles & Grid Background

**Files:**
- Modify: `dashboard/src/app/globals.css`

**Interfaces:**
- Produces: Global styles, font imports, grid background on body

- [ ] **Step 1: Write the failing test**
```bash
# Test: CSS builds without errors
cd dashboard && npx tailwindcss -o /dev/null 2>&1 | grep -c "error" || echo "0"
```

- [ ] **Step 2: Run test to verify it fails** (current globals.css is minimal)
Run: `cd dashboard && grep -c "Orbitron\|grid-pattern" src/app/globals.css || echo "0"`
Expected: 0

- [ ] **Step 3: Rewrite `dashboard/src/app/globals.css`** with:
- `@import "tailwindcss";`
- Google Fonts import for Orbitron (via @import url or <link> in layout)
- CSS custom properties for colors
- `.bg-grid-pattern` utility using SVG data URI
- Body: `font-family: 'Orbitron', monospace;` for headings, system mono for body
- `* { scrollbar-width: thin; scrollbar-color: #1a1a1a #000000; }`

- [ ] **Step 4: Verify CSS builds**
Run: `cd dashboard && npx tailwindcss -o /dev/null 2>&1`
Expected: No errors

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/app/globals.css
git commit -m "styles: add Orbitron font, grid pattern, monochrome base"
```

---

### Task 4: Update layout.tsx with MotionConfig & Font Link

**Files:**
- Modify: `dashboard/src/app/layout.tsx`

**Interfaces:**
- Consumes: globals.css
- Produces: RootLayout with `<html className="dark">`, MotionConfig

- [ ] **Step 1: Write the failing test**
```bash
# Test: layout compiles
cd dashboard && npx tsc --noEmit 2>&1 | grep -c "layout.tsx" || echo "0"
```

- [ ] **Step 2: Run test to verify it fails** (current layout has no MotionConfig)
Run: `cd dashboard && grep -c "MotionConfig\|Orbitron" src/app/layout.tsx || echo "0"`
Expected: 0

- [ ] **Step 3: Modify `dashboard/src/app/layout.tsx`**:
- Add `<link rel="preconnect" href="https://fonts.googleapis.com">`
- Add `<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">`
- Import `{ MotionConfig } from "framer-motion"`
- Wrap children in `<MotionConfig transition={{ type: "tween", ease: [0.25, 0.46, 0.45, 0.94] }}>`
- Add `className="dark antialiased"` to html

- [ ] **Step 4: Verify TypeScript compiles**
Run: `cd dashboard && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/app/layout.tsx
git commit -m "layout: add MotionConfig and Orbitron font"
```

---

### Task 5: Create BladeSlash Reusable Component

**Files:**
- Create: `dashboard/src/components/BladeSlash.tsx`

**Interfaces:**
- Produces: `BladeSlash` component — props: `className?: string`, `duration?: number`, `trigger?: "mount" | "hover"`

- [ ] **Step 1: Write the failing test**
```tsx
// Test file: dashboard/src/components/__tests__/BladeSlash.test.tsx
import { render, screen } from "@testing-library/react";
import { BladeSlash } from "@/components/BladeSlash";

test("renders blade slash element", () => {
  render(<BladeSlash />);
  expect(screen.getByTestId("blade-slash")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd dashboard && npm test -- --testPathPattern=BladeSlash 2>&1 | head -20`
Expected: FAIL (component doesn't exist)

- [ ] **Step 3: Create `dashboard/src/components/BladeSlash.tsx`**:
```tsx
"use client";
import { motion } from "framer-motion";

interface BladeSlashProps {
  className?: string;
  duration?: number;
  trigger?: "mount" | "hover";
}

export function BladeSlash({ className = "", duration = 0.6, trigger = "mount" }: BladeSlashProps) {
  const variants = {
    hidden: { x: "-100%", opacity: 0 },
    visible: { x: "100%", opacity: 1 },
    exit: { x: "100%", opacity: 0 },
  };

  return (
    <motion.div
      data-testid="blade-slash"
      className={`absolute inset-0 bg-[linear-gradient(135deg,transparent_48%,rgba(255,255,255,0.12)_50%,transparent_52%)] pointer-events-none ${className}`}
      initial={trigger === "mount" ? "hidden" : "visible"}
      animate={trigger === "mount" ? "visible" : "visible"}
      exit="exit"
      variants={variants}
      transition={{ duration, ease: [0.25, 0.46, 0.45, 0.94] }}
    />
  );
}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `cd dashboard && npm test -- --testPathPattern=BladeSlash`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/components/BladeSlash.tsx dashboard/src/components/__tests__/BladeSlash.test.tsx
git commit -m "feat: add BladeSlash animation component"
```

---

### Task 6: Create StatCard Component for Hero Live Stats

**Files:**
- Create: `dashboard/src/components/ui/StatCard.tsx`

**Interfaces:**
- Produces: `StatCard` component — props: `label: string`, `value: string | number`, `className?: string`

- [ ] **Step 1: Write the failing test**
```tsx
// Test file: dashboard/src/components/ui/__tests__/StatCard.test.tsx
import { render, screen } from "@testing-library/react";
import { StatCard } from "@/components/ui/StatCard";

test("renders label and value", () => {
  render(<StatCard label="Servers" value={1234} />);
  expect(screen.getByText("Servers")).toBeInTheDocument();
  expect(screen.getByText("1,234")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd dashboard && npm test -- --testPathPattern=StatCard 2>&1 | head -20`
Expected: FAIL

- [ ] **Step 3: Create `dashboard/src/components/ui/StatCard.tsx`**:
```tsx
"use client";
import { motion } from "framer-motion";
import { BladeSlash } from "@/components/BladeSlash";

interface StatCardProps {
  label: string;
  value: string | number;
  className?: string;
}

export function StatCard({ label, value, className = "" }: StatCardProps) {
  const formattedValue = typeof value === "number" ? value.toLocaleString() : value;
  return (
    <motion.div
      className={`relative flex flex-col items-center bg-dark-1/50 px-6 py-4 border border-dark-3/50 ${className}`}
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      whileHover={{ y: -2, borderColor: "silver" }}
    >
      <BladeSlash trigger="hover" duration={0.4} className="opacity-0 group-hover:opacity-100" />
      <p className="text-xs font-medium text-dark-silver tracking-wider uppercase">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white tabular-nums">{formattedValue}</p>
    </motion.div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `cd dashboard && npm test -- --testPathPattern=StatCard`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/components/ui/StatCard.tsx dashboard/src/components/ui/__tests__/StatCard.test.tsx
git commit -m "feat: add StatCard component for hero stats"
```

---

### Task 7: Rewrite Hero Component with Blade Slash Title, CTAs, Stats

**Files:**
- Modify: `dashboard/src/components/Hero.tsx`

**Interfaces:**
- Consumes: `BladeSlash`, `StatCard`
- Produces: Hero section with animated title, tagline, two CTAs, 4 stat cards

- [ ] **Step 1: Write the failing test**
```tsx
// Test file: dashboard/src/components/__tests__/Hero.test.tsx
import { render, screen } from "@testing-library/react";
import { Hero } from "@/components/Hero";

test("renders SCYTH title and tagline", () => {
  render(<Hero />);
  expect(screen.getByText("SCYTH")).toBeInTheDocument();
  expect(screen.getByText("Moderation")).toBeInTheDocument();
  expect(screen.getByText("Music")).toBeInTheDocument();
  expect(screen.getByText("Utilities")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd dashboard && npm test -- --testPathPattern=Hero 2>&1 | head -20`
Expected: FAIL (old Hero doesn't match new design)

- [ ] **Step 3: Rewrite `dashboard/src/components/Hero.tsx`** with:
- Section: `relative min-h-[70vh] flex flex-col items-center justify-center gap-8 px-6 pt-24 pb-16 bg-black overflow-hidden`
- Grid pattern background: `<div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none" />`
- Mount blade slash across full section
- Title: "SCYTH" with per-letter stagger animation (wrapping each letter in motion.span)
- Tagline: "Moderation • Music • Utilities" in `text-dark-silver font-mono`
- Two buttons: "Add to Discord" (solid white bg), "Commands" (outlined silver border)
- Live stats: 4 `StatCard` components in `flex flex-wrap gap-4 justify-center` — Servers, Users, Commands Used, Uptime (placeholder values, to be wired later)

- [ ] **Step 4: Run test to verify it passes**
Run: `cd dashboard && npm test -- --testPathPattern=Hero`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/components/Hero.tsx dashboard/src/components/__tests__/Hero.test.tsx
git commit -m "feat: rebuild Hero with blade slash title, CTAs, live stats"
```

---

### Task 8: Create Static Commands Data from main.py

**Files:**
- Create: `dashboard/src/lib/commands.ts`

**Interfaces:**
- Produces: `commandsData` array exported — each: `{ category: string; name: string; description: string; usage?: string }`

- [ ] **Step 1: Write the failing test**
```ts
// Test file: dashboard/src/lib/__tests__/commands.test.ts
import { commandsData } from "@/lib/commands";

test("has expected categories and commands", () => {
  expect(commandsData.length).toBeGreaterThan(30);
  const categories = [...new Set(commandsData.map(c => c.category))];
  expect(categories).toContain("Admin");
  expect(categories).toContain("Music");
  expect(categories).toContain("Utility");
  expect(categories).toContain("Config");
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd dashboard && npm test -- --testPathPattern=commands.test 2>&1 | head -20`
Expected: FAIL (file doesn't exist)

- [ ] **Step 3: Create `dashboard/src/lib/commands.ts`** by extracting from main.py COMMAND_SYNTAX:
- Map each command entry to `{ category, name, description, usage }`
- Categories: Admin, Music, Utility, Config, Security, VoiceMaster, Fun (match help menu)
- Use semicolon prefix `;ban` style from COMMAND_SYNTAX
- Export `commandsData` array and `categories` array

- [ ] **Step 4: Run test to verify it passes**
Run: `cd dashboard && npm test -- --testPathPattern=commands.test`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/lib/commands.ts dashboard/src/lib/__tests__/commands.test.ts
git commit -m "data: add static commands data from main.py COMMAND_SYNTAX"
```

---

### Task 9: Rewrite FeatureGrid Component with 5 Feature Cards

**Files:**
- Modify: `dashboard/src/components/FeatureGrid.tsx`

**Interfaces:**
- Consumes: `BladeSlash`, Lucide icons (ShieldCheck, Music, Terminal, Bot, Command)
- Produces: 5-card responsive grid with hover blade slash

- [ ] **Step 1: Write the failing test**
```tsx
// Test file: dashboard/src/components/__tests__/FeatureGrid.test.tsx
import { render, screen } from "@testing-library/react";
import { FeatureGrid } from "@/components/FeatureGrid";

test("renders all 5 features", () => {
  render(<FeatureGrid />);
  expect(screen.getByText("Moderation")).toBeInTheDocument();
  expect(screen.getByText("Music")).toBeInTheDocument();
  expect(screen.getByText("Utility")).toBeInTheDocument();
  expect(screen.getByText("Auto-Mod")).toBeInTheDocument();
  expect(screen.getByText("Custom Commands")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd dashboard && npm test -- --testPathPattern=FeatureGrid 2>&1 | head -20`
Expected: FAIL

- [ ] **Step 3: Rewrite `dashboard/src/components/FeatureGrid.tsx`**:
- Section: `py-16 bg-black`
- Container: `max-w-7xl mx-auto px-6`
- H2: "Features" in Orbitron `text-3xl font-bold text-white mb-12 text-center`
- Grid: `grid gap-6 sm:grid-cols-2 lg:grid-cols-3`
- 5 cards: each with Lucide icon (1px stroke, text-dark-silver), title, description
- Card: `relative h-48 flex flex-col items-center justify-center px-6 py-6 bg-dark-2 border border-dark-3 rounded-none transition-all duration-300`
- Hover: `whileHover={{ y: -2, borderColor: "silver" }}` + `BladeSlash trigger="hover"`

- [ ] **Step 4: Run test to verify it passes**
Run: `cd dashboard && npm test -- --testPathPattern=FeatureGrid`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/components/FeatureGrid.tsx dashboard/src/components/__tests__/FeatureGrid.test.tsx
git commit -m "feat: rebuild FeatureGrid with 5 cards and blade hover"
```

---

### Task 10: Rewrite CommandBrowser with Search, Tabs, Command List

**Files:**
- Modify: `dashboard/src/components/CommandBrowser.tsx`

**Interfaces:**
- Consumes: `commandsData`, `categories` from `@/lib/commands`
- Produces: Searchable, filterable command browser

- [ ] **Step 1: Write the failing test**
```tsx
// Test file: dashboard/src/components/__tests__/CommandBrowser.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { CommandBrowser } from "@/components/CommandBrowser";

test("filters by search", () => {
  render(<CommandBrowser />);
  const input = screen.getByPlaceholderText(/search commands/i);
  fireEvent.change(input, { target: { value: "ban" } });
  expect(screen.getByText(";ban")).toBeInTheDocument();
  expect(screen.queryByText(";play")).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd dashboard && npm test -- --testPathPattern=CommandBrowser 2>&1 | head -20`
Expected: FAIL

- [ ] **Step 3: Rewrite `dashboard/src/components/CommandBrowser.tsx`**:
- Section: `py-16 bg-black`
- Search input: `w-full px-4 py-3 bg-dark-1 border border-dark-3 rounded-none text-white placeholder-dark-silver focus:outline-none focus:ring-1 focus:ring-silver`
- Category tabs: Admin, Music, Utility, Config, Security, VoiceMaster, Fun — `px-4 py-2 bg-dark-2 border border-dark-3 rounded-none text-sm font-medium`
- Active tab: `border-silver bg-dark-1 text-white`
- Command list: `space-y-3` — each item `flex items-center gap-4 px-4 py-3 bg-dark-1 border border-dark-3 rounded-none`
- Left: command name `text-silver font-mono text-sm`
- Center: description `text-white text-sm flex-1`
- Right: category badge `text-xs text-dark-silver uppercase`
- Hover: blade slash + `border-silver`

- [ ] **Step 4: Run test to verify it passes**
Run: `cd dashboard && npm test -- --testPathPattern=CommandBrowser`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/components/CommandBrowser.tsx dashboard/src/components/__tests__/CommandBrowser.test.tsx
git commit -m "feat: rebuild CommandBrowser with search, tabs, command list"
```

---

### Task 11: Create NowPlaying Component (Listening To Card)

**Files:**
- Create: `dashboard/src/components/NowPlaying.tsx`

**Interfaces:**
- Produces: `NowPlaying` component — displays current track from placeholder data, blade hover

- [ ] **Step 1: Write the failing test**
```tsx
// Test file: dashboard/src/components/__tests__/NowPlaying.test.tsx
import { render, screen } from "@testing-library/react";
import { NowPlaying } from "@/components/NowPlaying";

test("renders listening to card", () => {
  render(<NowPlaying />);
  expect(screen.getByText(/listening to/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd dashboard && npm test -- --testPathPattern=NowPlaying 2>&1 | head -20`
Expected: FAIL

- [ ] **Step 3: Create `dashboard/src/components/NowPlaying.tsx`**:
- Card: `relative bg-dark-1 border border-dark-3 p-6 rounded-none`
- Header: "LISTENING TO" in `text-xs font-bold text-dark-silver tracking-wider`
- Track title: `text-lg font-bold text-white`
- Artist: `text-sm text-dark-silver`
- Duration/progress bar placeholder
- Hover: `BladeSlash trigger="hover"`

- [ ] **Step 4: Run test to verify it passes**
Run: `cd dashboard && npm test -- --testPathPattern=NowPlaying`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/components/NowPlaying.tsx dashboard/src/components/__tests__/NowPlaying.test.tsx
git commit -m "feat: add NowPlaying listening card"
```

---

### Task 12: Create /commands Route Page

**Files:**
- Create: `dashboard/src/app/commands/page.tsx`

**Interfaces:**
- Consumes: `CommandBrowser` component
- Produces: `/commands` route page

- [ ] **Step 1: Write the failing test**
```bash
# Test: route builds
cd dashboard && npx next build 2>&1 | grep -c "commands" || echo "0"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `ls dashboard/src/app/commands/page.tsx 2>/dev/null || echo "MISSING"`
Expected: MISSING

- [ ] **Step 3: Create `dashboard/src/app/commands/page.tsx`**:
```tsx
import { CommandBrowser } from "@/components/CommandBrowser";

export default function CommandsPage() {
  return (
    <main className="min-h-screen bg-black">
      <CommandBrowser />
    </main>
  );
}
```

- [ ] **Step 4: Verify build includes route**
Run: `cd dashboard && npx next build 2>&1 | tail -10`
Expected: Route `/commands` appears in output

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/app/commands/page.tsx
git commit -m "feat: add /commands route page"
```

---

### Task 13: Update page.tsx to Compose All Sections in Order

**Files:**
- Modify: `dashboard/src/app/page.tsx`

**Interfaces:**
- Consumes: `Hero`, `FeatureGrid`, `NowPlaying`, `CommandBrowser`
- Produces: Home page with sections in order: Hero → FeatureGrid → NowPlaying → CommandBrowser

- [ ] **Step 1: Write the failing test**
```tsx
// Test file: dashboard/src/app/__tests__/page.test.tsx
import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

test("renders all sections in order", () => {
  render(<Home />);
  expect(screen.getByText("SCYTH")).toBeInTheDocument();
  expect(screen.getByText("Features")).toBeInTheDocument();
  expect(screen.getByText(/listening to/i)).toBeInTheDocument();
  expect(screen.getByText("Command Browser")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd dashboard && npm test -- --testPathPattern=page.test 2>&1 | head -20`
Expected: FAIL (old page.tsx only has Hero, FeatureGrid, CommandBrowser)

- [ ] **Step 3: Rewrite `dashboard/src/app/page.tsx`**:
```tsx
import { Hero } from "@/components/Hero";
import { FeatureGrid } from "@/components/FeatureGrid";
import { NowPlaying } from "@/components/NowPlaying";
import { CommandBrowser } from "@/components/CommandBrowser";

export default function Home() {
  return (
    <main className="min-h-screen bg-black">
      <Hero />
      <FeatureGrid />
      <NowPlaying />
      <CommandBrowser />
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `cd dashboard && npm test -- --testPathPattern=page.test`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add dashboard/src/app/page.tsx dashboard/src/app/__tests__/page.test.tsx
git commit -m "feat: compose home page with all sections in order"
```

---

### Task 14: Build Verification & Dev Server Test

**Files:**
- None (verification only)

**Interfaces:**
- Verifies: Full build passes, dev server starts

- [ ] **Step 1: Run production build**
Run: `cd dashboard && npm run build`
Expected: Build completes without errors, all routes compiled

- [ ] **Step 2: Start dev server and verify**
Run: `cd dashboard && timeout 10 npm run dev 2>&1 | head -20`
Expected: "Ready on http://localhost:3000" (or configured PORT)

- [ ] **Step 3: Verify no TypeScript errors**
Run: `cd dashboard && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit any final fixes**
```bash
git add -A
git commit -m "chore: final build fixes and verification"
```

---

### Task 15: Verify bot-hosting.net Deployment Compatibility

**Files:**
- Verify: `main.py` dashboard startup unchanged

**Interfaces:**
- Verifies: `main.py` still launches dashboard correctly

- [ ] **Step 1: Check main.py dashboard launch code**
Run: `grep -A 10 "npm.*run.*dev" /workspaces/Scythe-project/main.py`
Expected: Subprocess exec with HOST/PORT env vars unchanged

- [ ] **Step 2: Verify dashboard package.json scripts unchanged**
Run: `cat dashboard/package.json | grep -A 5 '"scripts"'`
Expected: dev, build, start, lint present

- [ ] **Step 3: Test dashboard starts from project root**
Run: `cd /workspaces/Scythe-project && HOST=0.0.0.0 PORT=3000 npm --prefix dashboard run dev -- --help 2>&1 | head -5`
Expected: Next.js help output (verifies command works)

- [ ] **Step 4: Commit verification**
```bash
git commit --allow-empty -m "chore: verify bot-hosting.net deployment compatibility"
```

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-10-18-scyth-dashboard-overhaul.md`. Please review the plan. Which execution approach would you prefer?

- **Subagent-driven** - A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review.
- **Native** - I implement every task myself in this session, the way this harness runs work, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end.

For this plan I recommend **Native**, because the tasks are highly sequential (each component builds on the previous), interfaces are well-defined in the plan, and the codebase is small enough to hold in context. Does the plan capture what you want, and which approach should we use?