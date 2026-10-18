export const meta = {
  name: 'scyth-frontend-overhaul',
  description: 'Comprehensive frontend overhaul: music widget reactivity, scroll/layout viewport units, button consistency, dashboard/vault elevation',
  phases: [
    { title: 'Music Widget', detail: 'Fix now playing widget reactivity and empty/standby state in index.html' },
    { title: 'Scroll Layout', detail: 'Replace viewport units with 100dvh and fix scroll triggers in base.html/custom.css' },
    { title: 'Button Consistency', detail: 'Normalize border-radius, padding, tap targets across all buttons in custom.css and templates' },
    { title: 'Dashboard Vault', detail: 'Elevate commands module into interactive UI with search, categories, toggle states' },
    { title: 'Verify', detail: 'Review all changed files for correctness and regressions' },
  ],
};

phase('Music Widget');
const musicResult = await agent(`
You are editing the Scyth dashboard frontend. Work in /workspaces/Scythe-project/dashboard/templates/index.html.

TASK: Fix the Now Playing & Music Widget.

Current state:
- index.html lines 47-99: LISTENING TO card with track artwork, title, artist, progress bar, time-elapsed, time-duration spans.
- index.html lines 172-237: script with syncTrackData() fetching /api/now-playing every 3s, plus a setInterval updating progress bar every 1s.
- The API returns {hasData: false} when nothing is tracked. The JS if (data.hasData) block has NO else branch - when nothing plays, the UI retains stale values and never resets.
- time-elapsed and time-duration start as static 00:00.

Required changes:
1. In syncTrackData(), add an else branch for when !data.hasData: reset isLive=false, currentElapsed=0, totalDuration=0; set live-indicator to STANDBY (zinc-600 dot); reset progress-bar width to 0%; set time-elapsed and time-duration to 00:00; set title to dash and artist to No active session; dim the ambient glow.
2. When data.hasData is true but !data.isActive (last played), ensure progress bar shows 100% and elapsed shows full duration (already partially handled - verify).
3. Make the widget behave correctly when nothing is actively playing: show STANDBY state, do not show stale track data.
4. Keep all existing ID attributes (live-indicator, track-art, track-title, track-artist, progress-bar, time-elapsed, time-duration, ambient-glow) intact.

Do NOT change the HTML structure of the card itself - only fix the JS script block. Return a summary of exactly what you changed.
`, { agentType: 'general-purpose', label: 'fix-music-widget' });

phase('Scroll Layout');
const scrollResult = await agent(`
You are editing the Scyth dashboard frontend. Work in /workspaces/Scythe-project/dashboard/templates/base.html and dashboard/static/custom.css.

TASK: Fix Scroll & Layout Jumps.

Current state:
- base.html line 24: body class includes min-h-screen (equals 100vh, rigid viewport unit).
- custom.css: no 100vh or 100dvh usage found.
- The page uses Tailwind classes; min-h-screen causes layout jumps on mobile when the URL bar shows/hides.

Required changes:
1. In base.html, change body's min-h-screen to min-h-[100dvh] so the viewport uses dynamic units that account for mobile browser chrome.
2. Check custom.css for any fixed-height or 100vh patterns that could cause scroll jumps; if found, convert to 100dvh.
3. Check base.html for any state/re-render triggers that could reset scroll position. Report any found.
4. Do NOT remove or break the existing flex-col justify-between layout or sticky header/footer behavior.

Return a summary of exactly what you changed.
`, { agentType: 'general-purpose', label: 'fix-scroll-layout' });

phase('Button Consistency');
const buttonResult = await agent(`
You are editing the Scyth dashboard frontend. Work in /workspaces/Scythe-project/dashboard/static/custom.css and the HTML templates.

TASK: Fix Button & UI Consistency.

Current state:
- custom.css .neon-btn (line 1055): padding 0.5rem 1rem, border-radius 8px - but HTML overrides with inline Tailwind classes.
- index.html: DEPLOY SCYTH CORE = neon-btn px-8 py-3 text-lg; ACCESS SCYTH VAULT = neon-btn px-8 py-3 text-lg border...
- servers.html: CONFIGURE NODE / INITIATE CONNECTION = neon-btn w-full mt-4 text-xs font-semibold px-4 py-2
- settings.html: INITIATE PROTOCOL SAVE = neon-btn px-6 py-2.5 rounded-xl font-semibold text-xs
- base.html: Authorize button = px-4 py-2 text-xs; user dropdown = px-3.5 py-1.5

Required changes:
1. Update .neon-btn base CSS in custom.css to define consistent defaults: border-radius 12px, padding 0.75rem 1.5rem (px-6 py-3), min-height 44px for mobile tap targets, font-weight 600, font-size 0.95rem.
2. Normalize all hero/action buttons across templates to consistent padding (px-6 py-3), border-radius (rounded-xl), and font size (text-base) on desktop, with responsive reduction on mobile.
3. Ensure all buttons have minimum 44px tap targets (min-h-[44px] or equivalent) for mobile.
4. Keep the three button variants visually distinct but consistent: primary (neon gradient fill), secondary (border + transparent bg), tertiary (small header actions).
5. Do not break hover/active/transition states.

Return a summary of exactly what you changed in each file.
`, { agentType: 'general-purpose', label: 'fix-buttons' });

phase('Dashboard Vault');
const vaultResult = await agent(`
You are editing the Scyth dashboard frontend. Work in /workspaces/Scythe-project/dashboard/templates/commands.html.

TASK: Elevate Dashboard/Vault Architecture.

Current state:
- commands.html: SCYTH COMMAND VAULT page with 3 static category cards (DEFENSE, ENFORCE, UTILITY).
- Each card has a hardcoded grid of command text blocks (code + description) in neon-input-container divs.
- No search, no filtering, no categories toggle, no interactivity - just static text lists.

Required changes:
1. Add a search/filter input at the top of the command list that filters commands in real-time by name or description (client-side JS).
2. Add category filter chips/toggle buttons (DEFENSE / ENFORCE / UTILITY / ALL) that show/hide the corresponding category sections.
3. Make each command entry an interactive component: clicking the code copies it to clipboard (use navigator.clipboard.writeText with visual feedback).
4. Wrap each category in a clearly separated section with category headers.
5. Keep the existing visual styling (neon colors, elevated-card-enhanced, etc.) - don't break the bleed.bot-inspired aesthetic.
6. Preserve all existing command text and descriptions exactly as they are.

Add the search/filter and category toggle in vanilla JS at the bottom of the block (inside the {% endblock %} or a script tag). Return a summary of exactly what you changed.
`, { agentType: 'general-purpose', label: 'elevate-vault' });

phase('Verify');
const verifyResults = await parallel([
  () => agent(`Review /workspaces/Scythe-project/dashboard/templates/index.html after music widget fixes. Verify: (1) else branch handles !data.hasData, (2) timestamps reset to 00:00 when nothing playing, (3) progress bar resets, (4) STANDBY state shows correctly, (5) all ID attributes intact, (6) no syntax errors in the script. Report PASS/FAIL for each.`, { agentType: 'general-purpose', label: 'verify-music' }),
  () => agent(`Review /workspaces/Scythe-project/dashboard/templates/base.html after scroll/layout fixes. Verify: (1) min-h-[100dvh] replaces min-h-screen, (2) sticky header/footer still work, (3) flex-col justify-between intact, (4) no scroll-jump triggers. Report PASS/FAIL.`, { agentType: 'general-purpose', label: 'verify-scroll' }),
  () => agent(`Review /workspaces/Scythe-project/dashboard/static/custom.css and all HTML templates after button consistency fixes. Verify: (1) .neon-btn has consistent padding/border-radius/min-height, (2) all buttons across index.html, servers.html, settings.html, base.html use consistent tap targets (>=44px), (3) hover/active states preserved, (4) no broken classes. Report PASS/FAIL.`, { agentType: 'general-purpose', label: 'verify-buttons' }),
  () => agent(`Review /workspaces/Scythe-project/dashboard/templates/commands.html after dashboard vault elevation. Verify: (1) search/filter input present and functional, (2) category toggle chips present, (3) copy-to-clipboard on command code, (4) all original command text preserved, (5) JS has no syntax errors. Report PASS/FAIL.`, { agentType: 'general-purpose', label: 'verify-vault' }),
]);

return {
  musicResult,
  scrollResult,
  buttonResult,
  vaultResult,
  verifyResults: verifyResults.filter(Boolean),
};