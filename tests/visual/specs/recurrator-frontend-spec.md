# Recurrator — Front-End Implementation Spec

**Audience:** the web designer implementing `public/` · **Date:** November 2026
**Constraint that overrides everything:** the backend is frozen. No API change, no new endpoint, no new field.
**Ambition:** the front end should look and feel finished even where behaviour must be stubbed. Every stub is listed in §12 with its replacement point, so the backend team can find and replace each one with a single grep. S1 is additionally gated by one named constant.

---

## 1. Scope

### In scope
- Four screens: scope matrix (home), context list, task list, monster card.
- Rendered markup in `public/ui.js`; the four `.html` shells hold the mount points, the error slot, and the asset tags.
- All styling for the four screens in `public/styles/*.css`; the styleguide may use inline styles for its samples.
- An unlinked `styleguide.html` demonstrating every component and state.

### Out of scope (do not attempt)
- Monster artwork. One placeholder PNG, identical for every task. Art pipeline is a future iteration.
- Any write other than `POST /task/{id}/done`.
- Scope filtering (Work/Personal/Both). The URLs accept `?scope=`, the pages ignore it.
- Dark theme. Build for it (all colour via tokens) but do not design it.
- Desktop, tablet, landscape. Phone portrait only. Breaking at other widths is accepted.
- Editing a task, starring, skipping, adding or deleting anything.

---

## 2. Architecture

### Files (Option: flat in `public/`)
```
public/
  index.html            → scope matrix (NEW; was the context list)
  scope.html            → context list, scaffolded with ?scope=  (NEW, replaces old index.html)
  context.html          → task list (kept, restyled)
  task.html             → monster card plus the shared page header (kept, restyled)
  ui.js                 → every render* function (designer owns this file)
  main.js               → data flow, URLs, params, POST (designer does NOT open this file)
  styles/tokens.css     → :root custom properties only
  styles/components.css → cards, chips, badges, buttons, skeletons, empty/error
  styles/pages.css      → container, header, grids, page-level layout
  monster-placeholder.png
  styleguide.html       → not linked from the app; served by the static mount
```

### Load order in the four app pages
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="stylesheet" href="styles/tokens.css">
<link rel="stylesheet" href="styles/components.css">
<link rel="stylesheet" href="styles/pages.css">
...
<script src="ui.js"></script>
<script src="main.js"></script>
```

**Remove** the Pico CSS `<link>` and the inline `<style>` in `task.html`. **Add** the missing `<meta name="viewport">` — without it every phone renders the page at 980px and the entire design is zoomed out. This is the single highest-severity item in this document.

### The `ui.js` contract
Pure functions returning HTML strings. No fetching, no DOM queries, no global state.

```js
ui.renderScopeTile({ scope, label, emoji, dueCount, names })   // home
ui.renderScopeGrid(contexts, scope)                            // scope.html
ui.renderTaskList(tasks)                                       // context.html
ui.renderMonsterCard(task)                                     // task.html
ui.renderMarkdown(md)                                          // description → elements
ui.renderSkeleton(kind)                                        // 'tiles' | 'grid' | 'list' | 'card'
ui.renderEmpty(kind, ctx)                                      // 'grid' | 'list'
ui.renderError(err)                                            // never prints raw error text
ui.renderBreadcrumb(items)                                     // shared page header trail
ui.accentFor(name)                                             // → 'orange' | 'yellow' | … (hashed)
ui.monsterTitle(description)                                   // first 3 words, markdown-stripped
ui.dueState(task)                                              // → 'due' | 'not-due'
```

`main.js` keeps: URL building, `csv` passthrough, `getTodayISO()`, the breadcrumb item data, `POST /done`, and the `initPage()` dispatch. All rendered markup lives in `ui.*`; `main.js` assigns those strings and wires events.

---

## 3. Layout

- Container: `max-width: 420px; margin-inline: auto; padding: 20px;`
- No responsive breakpoints. The only media query is `prefers-reduced-motion` (§11).
- `padding-top: max(20px, env(safe-area-inset-top))`, `padding-bottom: max(20px, env(safe-area-inset-bottom))`.
- Page background: vertical gradient `#f6ecc9 → #f2e5bc → #ebdbb2`.
- Body text never below 11px; the 1-unit task oval is the documented 10px exception. Every tappable target ≥ 44×44 CSS px.
- Breadcrumb trail: a 12-unit row with 4px gaps; each oval is 24px high; the ancestor links use the 44px row height as their target (§5).

### Element sizes

| Element | CSS px |
|---|---|
| Page title (styleguide only) | 28 |
| Scope tile title | 25 |
| Monster card title | 23 |
| Section header | 14 |
| Body / row title | 15 |
| Secondary | 12 |
| Micro-label | **11** |
| Task oval label | **10** |
| Breadcrumb row | 44 |
| Breadcrumb oval | 24 |
| Page gutter | 20 |
| Home tile | 171×308 |
| Context card | 171×87 |
| Grid gap | 10 |
| Monster card | 327×458 min |
| Icon disc — tile | 40 |
| Icon disc — context card | 32 |
| Bounty badge diameter | 42 |
| Primary button height | **48** |

---

## 4. Tokens (`tokens.css`, no other file may contain a hex)

```css
:root{
  /* Gruvbox light */
  --c-bg-0:#fbf1c7; --c-bg-1:#f2e5bc; --c-bg-2:#ebdbb2;
  --c-bg-3:#d5c4a1; --c-bg-4:#bdae93; --c-bg-page:#f6ecc9;
  --c-surface:#fdf6d8;
  --c-ink:#3c3836;  --c-ink-2:#504945;
  --c-muted:#7c6f64; --c-faint:#a89984;

  --c-orange:#af3a03; --c-yellow:#b57614; --c-green:#79740e;
  --c-aqua:#427b58;   --c-blue:#076678;   --c-purple:#8f3f71; --c-red:#9d0006;

  /* semantic — never use the raw accents for state */
  --state-due: var(--c-orange);
  --state-not-due: var(--c-green);
  --state-starred: var(--c-yellow);

  --r-sm:10px; --r-md:18px; --r-lg:26px; --r-xl:34px;
  --shadow-card:0 9px 24px rgba(60,56,54,.20);
  --shadow-tile:0 12px 30px rgba(60,56,54,.24);
  --shadow-action:0 10px 26px rgba(175,58,3,.35);
  --border-card:1.5px solid rgba(60,56,54,.16);

  --fs-1:28px; --fs-2:25px; --fs-3:23px; --fs-4:16px;
  --fs-5:15px; --fs-6:14px; --fs-7:12px; --fs-8:11px; --fs-9:10px;

  --font-sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --font-mono:ui-monospace,"SF Mono",Menlo,monospace;
}
```

Rules:
- Semantic state colours only through `--state-*`. If a hex appears outside this file, it is a bug.
- Context accents are **decorative** and hashed (§10.1), never semantic.
- Tints are computed: `color-mix(in srgb, var(--accent) 15%, transparent)`.

---

## 5. Information architecture

```
index.html                          → 2×2 scope matrix
scope.html?scope=all|work|personal|both → context list (param inert today)
context.html?context=<name>         → task list for that context
task.html?id=<id>                   → monster card
```

- All four scope tiles are **live links** and send `?scope=<value>`. `scope.html` reads the param, uses it for the scope oval label, and **does not filter** (§12, stub S1).
- Breadcrumbs: one row of equal-height ovals. Home `Recurrator` (12 units); scope `Recurrator / <Scope>` (3 + 9); context `Recurrator / <Scope> / <Context>` (3 + 2 + 7); card `Recurrator / <Scope> / <Context> / #<id>` (3 + 2 + 6 + 1). The last oval present absorbs the units of the missing descendants; the current page is the filled last oval, the ancestors are links. The row has 4px gaps, 24px-high ovals, and no separators.
- Oval recipe: 12px sans with 10px horizontal padding; the 2-unit scope ancestor uses 12px with 2px padding, and the 1-unit task oval uses 10px mono with 2px padding. Ancestors use `--c-surface` fill and `--c-blue` text; the current page uses `--c-ink` fill and cream text. There is no border. The row is 44px tall and the ancestor links are the targets.

---

## 6. Screen 1 — Scope matrix (New `index.html`)

**Header:** the breadcrumb trail's only oval, `Recurrator`, filled and 12 units wide. There is no subtitle.

**Content:** 2×2 grid of tiles, gap 10px, tile 171×308, radius 34px, `--c-surface`, `--border-card`, `--shadow-tile`.

**Tile anatomy**
1. Icon disc 40px, left, on the same line as the title: fill `color-mix(accent 15%, transparent)`, ring `color-mix(accent 36%, transparent)`, emoji 24px, optically centred.
2. Title 25px/700, baseline on the disc's centreline. `Personal` is the longest — it must fit; size down to 20px before truncating.
3. Live count line (14px; it may wrap to two lines on a narrow tile): accent-coloured `n contexts due` · muted `due today`.
4. Divider 1px `rgba(60,56,54,.12)`.
5. Up to 4 due context names (15px), each with a 3px accent dot; `+n more` as a fifth line in `--c-faint`.
6. `OPEN ›` in mono 11px, bottom-left; chevron in accent, bottom-right.

**Data:** one `GET /context/?date=<today>` on load. `dueCount` = array length. Preview names = first 4, truncated with ellipsis. Only the All tile renders the count and names; the other three are live links with an empty body until the API returns a scope.
**Zero state:** count line reads `Victorious` in `--state-not-due`; preview list shows nothing.
**Loading:** 4 skeletons. **Error:** `Couldn't load` + retry.

Tiles and their accents: Work (💼, blue), Personal (🏡, green), Both (🔀, purple), All (🗂️, orange). These four accents are **fixed**, not hashed.

---

## 7. Screen 2 — Context list (New `scope.html`)

**Header:** `Recurrator` (3 units, link) + the scope display name (9 units, filled current). The label is `All`, `Work`, `Personal`, or `Both`; default `All` when the param is missing or unrecognised. There is no home glyph, subtitle, or count.

**Content:** 2-column grid, gap 10px, card 171×87, radius 18px, `--c-surface`, `--border-card`, `--shadow-card`.

**Card anatomy:** icon disc 32px + title 14px/600 on one line (shrink to 12px, then to 11px for very long names, then ellipsis — `doctoradoadmin` must survive), chevron right. **No second line, no counts.**
**Icon:** per-context emoji from a static map in `ui.js` (`activity 🏃`, `chores ✅`, `laptop 💻`, `gecicode 🛰️`, …; unmapped → `🗂️`).
**Accent:** `ui.accentFor(name)` (§10.1) drives the disc tint and the chevron.
**States:** loading → 4 skeletons; empty → *You are victorious!* / "Every monster has been exterminated."; error → retry card. Scroll fade at the bottom edge, `--c-bg-2` to transparent, 40px.

---

## 8. Screen 3 — Task list (`context.html`)

**Header:** `Recurrator` (3 units, link) + `<Scope>` (2 units, link) + `<Context>` (7 units, filled current). There is no separate `<h1>`; the filled context oval is the page identity.

**Content:** single-column rows, gap 9px, row ≈ 64px, radius 18px, `--c-surface`. Sorted by `coins` **descending** (unchanged from today).

**Row anatomy:** placeholder thumb 40×40 (radius 10, `object-fit: cover`) · title = `ui.monsterTitle(description)` 15px/600, one line, ellipsis · bounty chip right (pill, `--c-yellow` at 15% fill, mono 12px numeral with a 6px dot).
**No frame colour on rows** — every row here is due by definition, so state colour would be noise.
**States:** loading → 6 skeleton rows; empty → "No monsters left here." + back link; error → retry card.

---

## 9. Screen 4 — Monster card (`task.html`)

**Header:** mounted in `task.html` as `#pageHeader`: `Recurrator` (3 units, link) + `<Scope>` (2 units, link) + `<Context>` (6 units, link) + `#<id>` (1 unit, filled current, 10px mono). The card itself has no breadcrumb. The ID also appears in the `No. <id>` badge and the microtext.

**Card:** 327 wide and at least 458 high, radius 26px, `--c-surface`, `--border-card`, `--shadow-card`, frame 6px inset in the **state** colour (§10.4), plus a 1px hairline inset 2px.

**Anatomy top → bottom**
1. **Title** 23px/700 = `ui.monsterTitle(description)`, max 2 lines.
2. **Subtitle** 12px muted: `<context> · every <recurrence_days> days`.
3. **Bounty badge**, top-right, 42px: **circle** when not starred (`--state-starred` ink numeral on a 15% tint, 36% ring) · **star** when starred (solid `--state-starred` fill, cream numeral). `BOUNTY` label 11px mono under the shape. Display-only (§12, S3).
4. **Art panel** 295×164, radius 18px: tinted gradient + 6px pixel-checker overlay + placeholder PNG at 139×139, centred, with a 56×10 elliptical shadow beneath.
5. **Context chip** top-left of the art panel: emoji + context name, 12px, `--c-surface` at 94% behind it.
6. **`No. <id>`** badge bottom-right of the art panel, mono 11px.
7. **Stat grid 2×2**, labels 11px uppercase (`letter-spacing:.06em`, `--c-ink-2`), values 16px/700 `--c-ink`:
   `RECURRENCE` · `SKIP COUNT` · `DUE DATE` · `LATEST DONE`. Vertical 1px rule between columns.
8. **Status line** (§10.5), 12px, colour per state.
9. **Description** (`ui.renderMarkdown`) clamped to 4 lines, 14px, `--c-ink-2`. Check items are 44px label targets, so the clamp may show fewer items.
10. **Microtext** mono 11px `--c-faint`, right-aligned: `RCR-<id> · <context> · <n>d`.

**Actions (inline, under the card):**
- Primary, full width, 48px, radius 18px, `--state-due` fill, cream label `✓ Mark as Done`. While POSTing: `Saving…` + `disabled`. On success: `--state-not-due` fill, `Done today ✓`, `disabled` until reload. `aria-live="polite"` on the label.
- Secondary, full width, 48px, `--c-surface`, `--border-card`: `✎ Edit monster`. Rendered and styled, `aria-disabled="true"`, no handler (§12, S4).

---

## 10. Behaviour rules

### 10.1 Accent hashing
```js
// lowercase, trimmed name; sum of char codes; mod 7
const ACCENTS = ['orange','yellow','green','aqua','blue','purple','red'];
function accentFor(name){
  let s = 0; for (const ch of name.toLowerCase().trim()) s += ch.charCodeAt(0);
  return ACCENTS[s % 7];
}
```
`activity` → 877 → `green`. Deterministic, no storage. Adjacent cards may collide; that is accepted, not a bug.

### 10.2 Title from description
1. Strip markdown syntax and leading list markers / numbering.
2. Take the first 3 whitespace-separated words of the first non-empty line.
3. Capitalise the first letter. No ellipsis. Fewer than 3 words → use all of them.

### 10.3 Markdown subset (`ui.renderMarkdown`)
Supported: paragraphs, `**bold**`, `_italic_`, `` `code` ``, `- ` lists, `- [ ]` / `- [x]` check lists, `[text](url)`, line breaks. Everything else renders literally.
- **Escape HTML before transforming.** Descriptions are user data.
- **Decode the CSV line-break escape first.** The data stores a line break as the two characters backslash and n; the renderer turns them into a newline before block parsing, so a single escape breaks a line inside one paragraph and a double escape separates paragraphs.
- Links: `target="_blank" rel="noopener noreferrer"`.
- Check lists: real `<input type="checkbox">`, checked from the markdown, **toggling is local-only and not persisted** (§12, S5). Box styled with `accent-color: var(--c-orange)`; label text follows.

### 10.4 Due state
```js
due_date <= getTodayISO()  → 'due'      (orange frame, --state-due)
due_date >  getTodayISO()  → 'not-due'  (green frame, --state-not-due)
no due_date                → no frame   (defensive default)
```
Basis: `getTodayISO()`, `America/Los_Angeles`. No severity levels, no third colour, no extra severity cue. The backend asserts a fourth date, so the app cannot serve the no-due-date state; the styleguide demonstrates it as the defensive default.

### 10.5 Status line copy
| Condition | Text | Colour |
|---|---|---|
| done today or yesterday | `Done yesterday` / `Done today` | `--state-not-due` |
| `due_date` < today | `Overdue by 3 days` (days<30), `Overdue by 3 months` (≥30) | `--state-due` |
| `due_date` == today | `Due today` | `--state-due` |
| future | `Due in 12 days` (days≤45), else `Due in 3 months` | `--c-muted` |

Month counts are `floor(days / 30)` and are pluralised.

Dates in the stat grid stay **ISO** (`2026-08-10`) — the status line is the human-readable one.

### 10.6 Done flow
`POST /task/{id}/done` → on 2xx re-fetch the task and re-render in place (no navigation). On failure: button returns to `✓ Mark as Done`, an inline message `Didn't save. Try again.` appears directly under the button, raw error to `console.error`.

---

## 11. Accessibility

- Every target ≥ 44×44 CSS px. The breadcrumb row is 44px tall; the Recurrator, Scope, and Context ancestor cells are at least 44px wide. The current ovals and the 1-unit task oval are not links. The current page carries `aria-current="page"`.
- Star badge: `aria-label="Starred"` / `aria-label="Not starred"`; not a button.
- Decorative discs, dots, chevrons: `aria-hidden="true"`.
- Contrast: `--c-ink` on `--c-surface` = 8.6:1. `--c-muted` on `--c-surface` = 4.6:1 (body ok, not for 11px labels — those use `--c-ink-2` or `--c-faint` only for non-essential text). Verify every pairing before handoff.
- Focus visible on all links and buttons: 2px `--c-blue` offset 2px.
- `prefers-reduced-motion`: no transitions beyond colour changes.
- No colour-only information: state is always also in text (status line, labels).

---

## 12. Stub register (the deliberate lies)

| # | Stub | Where | Replace with |
|---|---|---|---|
| S1 | `?scope=` is read but never filters; the scope oval label changes | `main.js: applyScope()` | filter by `context.scope` |
| S2 | Placeholder PNG for every monster | `ui.js` | sprite/art lookup |
| S3 | Bounty badge is a status indicator, not a star toggle | `ui.renderMonsterCard` | `PATCH /task/{id}/star` |
| S4 | `Edit monster` is `aria-disabled="true"`, no handler | `ui.renderMonsterCard` | `edit.html` + `PATCH /task/{id}` |
| S5 | Check lists toggle in memory only | `ui.renderMarkdown` | `PATCH /task/{id}` notes |
| S6 | Context roster/emoji map is hardcoded | `ui.js: CONTEXT_META` | derive from API |

S1 is gated by one exported constant so the future flip is obvious. S2–S4 stay documented stubs with their own replacement points:
```js
const SCOPES_ACTIVE = false;  // S1 — set true when the API returns `scope`
```

---

## 13. Styleguide page (`styleguide.html`, unlinked)

Must show, each labelled:
1. Every token swatch (bg 0–4, page gradient, surface, ink scale, 7 accents, every state colour in §4).
2. Every type style at its size.
3. Home tile — normal, zero-due.
4. Context card — short name, long name (`doctoradoadmin`), each accent.
5. Task row — short, long (truncated), with bounty.
6. Monster card — not-due/unstarred, due/starred, overdue/starred, no-due-date.
7. Markdown rendering — all seven supported constructs.
8. Buttons — primary, saving, done, secondary-disabled.
9. Skeleton, empty, error.
10. Breadcrumb — home, scope, context, card trails; current/ancestor; long `Personal` and `doctoradoadmin`; `#999` task.

---

## 14. Definition of done

1. Four screens render at 393px with no horizontal scroll and nothing clipped.
2. The four headers use the 12-unit oval trail: home 12; scope 3+9; context 3+2+7; card 3+2+6+1. The card header is in `#pageHeader`; there is no home glyph, page title, subtitle, or header count.
3. `grep -E "#[0-9a-fA-F]{3,6}" styles/components.css styles/pages.css` → no results.
4. No network requests except the API (no CDN, no fonts, no Gravatar) — verified in DevTools.
5. Every state in §13 visually verified.
6. All targets ≥44px; the breadcrumb ancestor links meet 44×44; contrast checked; keyboard focus visible.
7. `main.js` may add the page initialisers and data flow the new information architecture needs. No rendering logic may live in it.
8. `<meta name="viewport">` present in all four HTML files; Pico `<link>` gone.
9. The current page oval is filled and every ancestor is a link; `Personal` fits the 2-unit scope oval and `#999` fits the 1-unit task oval.

---

## 15. Decisions still open (defaults in brackets)

| # | Question | Default if unanswered |
|---|---|---|
| O1 | Retry = full `location.reload()` or a re-run of the page init? | `location.reload()` — zero logic |
| O2 | Files flat in `public/` or nested in `public/styles`, `public/js`? | flat, except styles |
| O3 | Home tile at 0 due: `Victorious` or `Nothing due`? | `Victorious` |
| O4 | Empty `scope.html`: message only, or also list contexts with nothing due? | message only (listing needs N+1) |
| O5 | Does the task list keep `coins` on the row *and* in the card badge? | yes — ranking vs reward |
| O6 | Description clamp on the card: 4 lines with no expander? | yes, 4 lines, no expander |
| O7 | Emoji per context: fixed map of the full roster, or a generic 🗂️ for all? | fixed map |
