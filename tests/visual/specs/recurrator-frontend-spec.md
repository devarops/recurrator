# Recurrator — Front-End Implementation Spec

**Date:** November 2026
**Audience:** the web designer implementing `public/`
**API posture:** the API is a dependency, not a frozen constraint. The frontend uses only the calls in §2.4, which follow the documented interface: an undated collection is an inventory, a dated collection is a due view. Where it needs a field or endpoint the API does not yet return, the need is a numbered dependency in §13.3. Every dependency has a working fallback.
**Ambition:** the front end should look and feel finished even where behaviour must be stubbed. Every stub is listed in §13.2 with its replacement point, so the backend team can find and replace each one with a single grep.

> **Status of the search screen.** §10 is the specified target but is not yet in the visual capture matrix or the approved PNG baseline. The four existing screens remain the current approved baseline; search captures and browser tests land in the next frontend loop.

---

## 0. Decision log

These decisions supersede the four-screen spec and the unmerged v3.2 draft wherever they disagree.

| # | Decision |
|---|---|
| Q1 | Five screens: home, scope, context, card, **search**. |
| Q2 | One width contract: `max-width: 420px`, fluid below it. The capture reference stays 393px; there are no separate 393/443 layout variants and no width-specific media queries. |
| Q3 | Breadcrumb uses the v3.2 geometry: 32px ovals, content-sized ancestors, the current oval absorbing the remainder, a 48px magnifier reserve, and `…` collapse. |
| Q4 | The actual `?scope=` is carried through context, card, and search trails, defaulting to `All`. |
| Q5 | All four home tiles count and preview their due contexts through their own scope view, and the scope list filters through the same views. The `all` view is the alias for the whole context collection. |
| Q6 | The task list uses the dated due view of one context, preserves its API order, never sorts client-side, and never prefetches. |
| Q7 | The card keeps `LATEST DONE` and uses `latest_date` as the fallback. `D5` requests `latest_done_date` (`date_4`) for both the stat and the done status. |
| Q8 | A 409 completion re-fetches the task and shows the actual state. |
| Q9 | One celebratory empty state is reused for both lists: “You are victorious!” / “You have vanquished all the monsters!” |
| Q10 | Search uses `D6 = GET /search/?query={string}` returning full task objects. The browser applies the context/scope pills and the Sort control; the server matches the description only. |
| Q11 | Search keeps URL state (`query`, `context`, `scope`, `sort`) and a sticky trail + field, but does **not** restore scroll position. Its count row shows `<n> tasks` only; “Clear all” returns to bare `search.html`. |
| Q12 | Token role-based swap: drop `--c-bg-3`, `--c-bg-4`, `--c-ink-2`; rename `--c-bg-0` to `--c-cream`; drop the 28px and 10px type sizes; add no new colour or derived tokens. |
| Q13 | Search is specified now; its capture and browser tests follow later. No `DOCS.md` or `CHANGELOG.md` entry until the API fields/endpoints exist. |
| Q14 | The frontend adopts the path-based interface: `/context/` is the full roster, `/context/{id}` is a read-only roster, and `/context/{id}/due/{date}` is the only context call that writes. |
| Q15 | Every dated call carries an explicit date in the path, because captures pin the date; the undated `/due/` aliases serve people typing URLs, not the app. |

---

## 1. Scope

### In scope
- Five screens: scope matrix (home), context list, task list, monster card, search.
- Rendered markup in `public/ui.js`; the five `.html` shells hold the mount points, the error slot, and the asset tags.
- All styling for the five screens in `public/styles/*.css`; the styleguide may use inline styles for its samples.
- An unlinked `styleguide.html` demonstrating every component and state.

### Out of scope (do not attempt)
- **Server work of any kind**: endpoints, fields, bulk routes, server-side search, persistence. Record the need in §13.3 instead.
- Monster artwork. One placeholder PNG for every task.
- Any write other than `POST /task/{id}/done`. The dated due view of a context writes skip data on the server; that is an API fact, not a frontend write.
- Dark theme. Build for it (all colour via tokens) but do not design it.
- Desktop, tablet, landscape. Phone portrait only; the layout is fluid up to the 420px cap.
- Editing a task, starring, skipping, adding or deleting anything.

---

## 2. Architecture

### 2.1 Files (flat in `public/`)

```
public/
  index.html            → scope matrix (home)
  scope.html            → context list, scaffolded with ?scope=
  context.html          → task list
  task.html             → monster card plus the shared page header
  search.html           → search over all tasks
  ui.js                 → every render* function (designer owns this file)
  main.js               → data flow, URLs, params, POST, caches (designer does NOT open this file)
  styles/tokens.css     → :root custom properties only
  styles/components.css → cards, chips, badges, buttons, skeletons, empty/error
  styles/pages.css      → container, header, grids, page-level layout
  monster-placeholder.png
  styleguide.html       → not linked from the app; served by the static mount
```

### 2.2 Load order in the five app pages

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="stylesheet" href="styles/tokens.css">
<link rel="stylesheet" href="styles/components.css">
<link rel="stylesheet" href="styles/pages.css">
...
<script src="ui.js"></script>
<script src="main.js"></script>
```

**Remove** the Pico CSS `<link>` and the inline `<style>` in `task.html`. **Add** the missing `<meta name="viewport">` — without it every phone renders the page at 980px and the whole design is zoomed out. This is the single highest-severity item in this document.

### 2.3 The `ui.js` contract

Pure functions returning HTML strings. No fetching, no DOM queries, no global state.

```js
ui.renderBreadcrumb(items)                        // items: {label, emoji?, href?|null, kind}
ui.renderScopeTile({ scope, label, emoji, dueCount, names })
ui.renderScopeGrid(contexts, scope)
ui.renderTaskList(tasks)                          // context.html: server order, untouched
ui.renderTaskRow(task)                            // single height, meta = context · status
ui.renderMonsterCard(task)
ui.renderSearchFrame({ q, level, active, count, loading })   // field + pills + count row
ui.renderFilterPills(items, active)               // wraps; active value omitted
ui.renderMarkdown(md)
ui.renderSkeleton(kind)                           // 'tiles' | 'grid' | 'list' | 'card'
ui.renderEmpty(kind, ctx)                         // one celebratory state for both lists
ui.renderError(err)                               // never prints raw error text
ui.accentFor(name)                                // → 'orange' | 'yellow' | … (hashed)
ui.monsterTitle(description)                      // first 3 words, markdown-stripped
ui.dueState(task)                                 // → 'due' | 'not-due'
ui.statusLine(task)                               // §11.5
ui.contextMeta(name)                              // { emoji, scope } from the static map; the scope views confirm it
```

`main.js` keeps: URL building, `csv` passthrough, `getTodayISO()`, breadcrumb data, the summary cache (§2.5), the search index, `POST /done`, search URL state, `initPage()`.

### 2.4 API facts the UI is built on

The interface below is the documented one. The running service still answers the older query-based forms, so `main.js` changes its URL builders in one place when the path-based routes ship.

| Call | Returns | Used by | Caution |
|---|---|---|---|
| `GET /task/` | **ids only**, 223 today | search catalogue | not a summary — every row needs a second call |
| `GET /task/due/{date}` | due and overdue ids, file order | not used today | read-only |
| `GET /task/{id}` | `description`, `context`, `due_date`, `coins`, `starred`, `latest_date`, `rating`; `D5` adds `latest_done_date` | cards, both lists | N+1 by design |
| `GET /context/` | every context named in the file | search pills | not a due view |
| `GET /context/due/{date}` | due and overdue context names, alphabetical | not used today — the `all` view covers it | due only — never a full roster |
| `GET /context/{id}` | every task id in the context, file order | not used today — the due view is the list source | read-only; the only context call safe for enumeration |
| `GET /context/{id}/due/{date}` | prioritized ids, **WIP-limited**, and it **writes** `skip_count`/`skip_date` | task list only | see R1, R2, R4 |
| `GET /scope/` | stored scope names (`both`, `personal`, `work`) | not used today — the four scopes are fixed | the `all` alias is not listed |
| `GET /scope/{scope_id}/` | contexts in a scope that have tasks, alphabetical | search scope map | `scope_id` is a stored scope or `all` |
| `GET /scope/{scope_id}/due/{date}` | due contexts in a scope | home, scope list | `all` matches `/context/due/{date}` |
| `POST /task/{id}/done` | new `due_date`, `rating`; **409** if done today or yesterday | card | see §11.6 |

**R1** Never call `/context/{id}/due/{date}` to enumerate or search: it mutates the data file and truncates the result. Use `/context/{id}` for the roster.
**R2** Preserve the order returned by `/context/{id}/due/{date}` — it encodes WIP priority and deferral. No client sort.
**R3** `due_date` is always computable (`latest_date + recurrence_days`); “no due date” is a styleguide-only state.
**R4** Never prefetch a task list; loading `context.html` for a context is a write to the due view.
**R5** `latest_date` is the later of the last completion and the skip date. The card’s `LATEST DONE` target is `latest_done_date` (`date_4`), requested by `D5`; until it exists, the fallback is `latest_date` and the discrepancy is known.
**R6** An absent context or scope returns 404. Show the error state, never an empty list.
**R7** Every dated call carries an explicit date from `getTodayISO()`, so captures and tests stay deterministic.

### 2.5 The task summariser (one data path, three screens)

```
summaries(ids) → [{ id, context, description, due_date, coins, starred, latest_date, latest_done_date? }]
```

- Pool of **6** concurrent requests; renders per arrival; never blocks on the whole set.
- `Map` in memory + `sessionStorage` (`recurrator.summaries.v1`), TTL **5 min**, invalidated after a successful `POST /done` or after a 409 re-fetch.
- `context.html` calls it with the ids returned by `/context/{id}/due/{date}` (up to the WIP limit of 6); `search.html` with 223 in the fallback; the card fetches its own task.
- When `D6` lands, search uses it instead of `GET /task/` plus `summaries()`; the render functions do not move.

---

## 3. Layout

### 3.1 Container
- `max-width: 420px; margin-inline: auto; padding: 20px;`
- `padding-top: max(20px, env(safe-area-inset-top))`, `padding-bottom: max(20px, env(safe-area-inset-bottom))`.
- Page background: vertical gradient `--c-bg-page → --c-bg-1 → --c-bg-2`.
- No responsive breakpoints. The only media query is `prefers-reduced-motion` (§12).
- The capture reference is 393px; the container is fluid up to 420px. There are no separate 393/443 variants and no width-specific media queries.
- Body text never below 11px. Every tappable target ≥ 44×44 CSS px.

### 3.2 Element sizes

| Element | CSS px |
|---|---|
| Page title (styleguide only) | 25 |
| Scope tile title | 25 |
| Monster card title | 23 |
| Search field text | **16** (prevents iOS zoom-on-focus) |
| Body / row title | 15 |
| Section header | 14 |
| Secondary | 12 |
| Micro-label | **11** |
| Task oval label | **11** |
| Header row / pill row height | 44 |
| Breadcrumb oval height | 32 |
| Filter pill height | 32 |
| Pill gap (inline and block) | 8 |
| Page gutter | 20 |
| Home tile | 171×308 at the 393 reference; grid cell is `1fr` and widens to the 420 cap |
| Context card | 171×87 at the 393 reference; grid cell is `1fr` and widens |
| Grid gap | 10 |
| Monster card | 327×458 min |
| Search field / primary button | 48 |
| Task row | **64, one height only** |
| Icon disc — tile | 40 |
| Icon disc — context card | 32 |
| Row thumb | 40 |
| Bounty badge diameter | 42 |
| Emoji advance in a row's meta | **1.15em + 4px** |

---

## 4. Tokens (`tokens.css` — no other file may contain a hex)

```css
:root{
  /* Backgrounds */
  --c-bg-page:#f6ecc9; --c-bg-1:#f2e5bc; --c-bg-2:#ebdbb2;
  --c-surface:#fdf6d8; --c-cream:#fbf1c7;

  /* Text */
  --c-ink:#3c3836;  --c-muted:#74675c; --c-faint:#a89984;

  /* Accents — decorative, hashed */
  --c-orange:#af3a03; --c-yellow:#b57614; --c-green:#79740e;
  --c-aqua:#427b58;   --c-blue:#076678;   --c-purple:#8f3f71; --c-red:#9d0006;

  /* Semantic — never use the raw accents for state */
  --state-due: var(--c-orange);
  --state-not-due: var(--c-green);
  --state-starred: var(--c-yellow);

  --r-sm:10px; --r-md:18px; --r-lg:26px; --r-xl:34px;
  --shadow-card:0 9px 24px rgba(60,56,54,.20);
  --shadow-tile:0 12px 30px rgba(60,56,54,.24);
  --shadow-action:0 10px 26px rgba(175,58,3,.35);
  --border-card:1.5px solid rgba(60,56,54,.16);

  --fs-2:25px; --fs-3:23px; --fs-4:16px;
  --fs-5:15px; --fs-6:14px; --fs-7:12px; --fs-8:11px;

  --font-sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --font-mono:ui-monospace,"SF Mono",Menlo,monospace;
}
```

Rules:
- Semantic state colours only through `--state-*`. If a hex appears outside this file, it is a bug.
- Context accents are **decorative** and hashed (§11.1), never semantic.
- Tints, hairlines, art overlays and rings are computed inline with `color-mix()`; they are **not** new tokens.
- `--c-muted` is 5.0:1 on `--c-surface` and is the 11px label colour. `--c-faint` is 2.3:1 and is non-essential text only.
- Pill radius is `999px` inline; it is not a token.
- `--c-cream` replaces the old `--c-bg-0` and is the text colour on `--c-ink` ovals and coloured buttons.
- The token list is a closed set. Adding a colour or derived token requires removing one first.

---

## 5. Information architecture and the header

```
index.html                               → 2×2 scope matrix
scope.html?scope=all|work|personal|both  → context list
context.html?context=<name>&scope=       → task list for that context
task.html?id=<id>&scope=                 → monster card
search.html?query=&context=&scope=&sort= → search over all tasks
```

### 5.1 Trails

| Screen | Trail |
|---|---|
| Home | `Recurrator` (current) |
| Scope | `Recurrator` / `<Scope>` (current) |
| Context | `Recurrator` / `<Scope>` / `<Context>` (current) |
| Card | `Recurrator` / `<Scope>` / `<Context>` / `#<id>` (current) |
| Search, from home or a scope | `Recurrator` / `<Scope>` / `Search` (current) |
| Search, from a context | `Recurrator` / `<Scope>` / `<Context>` / `Search` (current) |

The card trail is hierarchical regardless of entry point. The card and search screens have no magnifier.

### 5.2 Oval recipe — no "units"

- Row: `display:flex; align-items:center; gap:4px; height:44px; min-width:0;`
- Oval: `height:32px; border-radius:999px; padding-inline:12px; font:600 12px/1 var(--font-sans); white-space:nowrap;`
- **Ancestors are content-sized** (`flex:0 0 auto`): `<a>` filling the 44px row, `min-width:44px`, `max-width:40%`, `overflow:hidden; text-overflow:ellipsis` — `--c-surface` fill, `--c-blue` text.
- **The current oval absorbs the remainder**: `flex:1 1 auto; min-width:max-content;` — `--c-ink` fill, `--c-cream` text, label centered, `aria-current="page"`, not a link. It is the screen's title bar, which is why no screen declares an `<h1>`.
- **Reserve before measuring**: the row keeps `44px + 4px` free at its right edge for the magnifier (§5.3). With no magnifier — card and search — the current oval runs to the content edge.
- `#<id>` inherits the stretch like any other current oval, and is the one oval that may never be truncated.
- **Collapse applies to the ancestors only**: if they overflow, middle ancestors become one non-link `…` oval (`aria-hidden`, `title` = full trail) *before* the current oval is allowed to shrink below `min-content`.

### 5.3 The magnifier

Present on home, scope list and task list; **absent on the card and on the search page**. It is a link to `search.html` carrying the current context (`&context=`), the current scope (`&scope=`), or nothing (home). 44×44 target, `aria-label="Search"`, pinned to the right of the header row; the trail reserves `calc(100% - 48px)` before §5.2's collapse rule measures.

### 5.4 The trail is a control on `search.html` only

On the search page the trail states the active filter and doubles as the widening control — and it must look different where it behaves differently, or it is a trap.

- An oval representing an **active, removable filter** is a `<button>`, announced `Clear <label> filter`. Activating it drops that filter **and every filter nested inside it**.
- An oval with nothing to clear is plain text: not focusable, no role.
- `Recurrator` stays a link home; `Search` is the current page.
- **No `×` glyph.** The affordance is carried by fill and text colour: interactive ovals use `--c-blue` on `--c-surface`; the inert context oval uses `--c-muted` on `color-mix(in srgb, var(--c-bg-2) 55%, transparent)`. The distinction is real in the accessibility tree (`button` vs `span`), so the colour difference is a hint, not the information.

Behaviour:

```
Recurrator / All / telefono / Search   → tap `All`        → Recurrator / All / Search
                                       → tap `telefono`   → inert, nothing
Recurrator / Work / telefono / Search  → tap `Work`        → Recurrator / Work / Search
Recurrator / Work / Search             → tap `Work`        → inert; widen with the `All` pill
```

Tapping a pill *narrows*; tapping the scope oval *widens*. That is the whole interaction model.

---

## 6. Screen 1 — Scope matrix (`index.html`)

**Header:** the trail's only oval, `Recurrator`, filled, plus the magnifier.
**Content:** 2×2 grid, gap 10, tile min-height 308, radius 34, `--c-surface`, `--border-card`, `--shadow-tile`. Grid cells are `1fr`, so they widen up to the 420px cap.

**Tile anatomy**
1. Icon disc 40px on the title line: accent tint fill, accent ring, emoji 24px.
2. Title 25/700, baseline on the disc centreline; `Personal` must fit (shrink to 20 before truncating).
3. Count line 14px, may wrap: accent `n contexts due` · muted `due today`.
4. Divider: 1px `color-mix(in srgb, var(--c-ink) 12%, transparent)`.
5. Up to 4 due context names (15px) with a 3px accent dot; `+n more` in `--c-faint`.
6. `OPEN ›` mono 11 bottom-left, chevron accent bottom-right.

**Data:** one `GET /scope/{scope_id}/due/{date}` per tile, with `all` for the last one. **Every tile counts and previews the contexts its own view returns**: four tiles, four numbers, and the four counts sum to the `All` count because the stored scopes partition the contexts.
**Zero state:** `Victorious` in `--state-not-due`; no names.
**Loading:** 4 skeletons. **Error:** `Couldn't load` + retry.
**Tiles:** Work (💼, blue), Personal (🏡, green), Both (🔀, purple), All (🗂️, orange) — fixed accents.

---

## 7. Screen 2 — Context list (`scope.html`)

**Header:** `Recurrator` (link) / scope name (current), plus the magnifier.
**Content:** 2-column grid, gap 10, card min-height 87, radius 18, `--c-surface`, `--border-card`, `--shadow-card`. Grid cells are `1fr`.
**Card:** icon disc 32 + title 14/600 (shrink to 12, then 11, then ellipsis — `doctoradoadmin` survives), chevron. No second line, no counts.
**Accent:** `ui.accentFor(name)`.
**Data:** `GET /scope/{scope_id}/due/{date}` for the active scope, `all` included. The API filters the list, so a scope with nothing due renders the empty state.
**States:** loading → 4 skeletons; empty → the celebratory state (§9); error → retry card; 40px bottom fade.

---

## 8. Screen 3 — Task list (`context.html`)

**Header:** `Recurrator` (link) / `<Scope>` (link) / context (current), plus the magnifier — which carries `&context=<context>` into search.
**Source:** `GET /context/{id}/due/{date}` → ids → `summaries(ids)`. This call **writes** (R1, R4): no prefetch, no polling.
**Order:** exactly the API order (R2). No client sort.
**Row:** thumb 40×40 (radius 10) · `ui.monsterTitle(description)` 15/600, one line, ellipsis · bounty chip right (pill, `--c-yellow` at 15% fill, mono 12px numeral with a 6px dot). One height, 64px.
**No state colour on rows** — inside a context everything is due.
**Empty:** the celebratory state, no back link: “You are victorious!” / “You have vanquished all the monsters!”
**States:** loading → 6 skeletons; error → retry.

---

## 9. Screen 4 — Monster card (`task.html`)

**Header:** `#pageHeader`: `Recurrator` (link) / `<Scope>` (link) / context (link) / `#<id>` (current, mono 11). **No magnifier.**

**Card:** 327 × min 458, radius 26, `--c-surface`, `--border-card`, `--shadow-card`, 6px inset frame in the state colour (§11.4), plus a 1px hairline inset 2px.

1. **Title** 23/700 = `ui.monsterTitle(description)`, max 2 lines.
2. **Bounty badge** 42px top-right: circle when unstarred (`--state-starred` numeral on 15% tint, 36% ring); star when starred (solid, cream numeral). `BOUNTY` 11px mono beneath. Display-only (S3).
3. **Art panel** 295×164, radius 18: tinted gradient + 6px checker + placeholder PNG 139×139 centred, 56×10 elliptical shadow.
4. **Rating** badge bottom-right of the panel, mono 11, hidden `Rating` prefix.
5. **Stat grid 2×2**, labels 11 uppercase `.06em` `--c-muted`, values 16/700, vertical rule between columns: `RECURRENCE` · `SKIP COUNT` · `DUE DATE` · `LATEST DONE`.
6. **Status line** (§11.5) 12px.
7. **Description** `ui.renderMarkdown`, clamped 4 lines, 14px `--c-muted`.

**`LATEST DONE`:** the target value is `latest_done_date` (`date_4`), requested by `D5`. Until the API exposes it, the card displays `latest_date` and the known discrepancy is documented in §13.3. `due_date` continues to use `latest_date` internally; the frontend does not recompute it.

**Actions:** primary 48px `--state-due` → `Saving…` → `--state-not-due` `Done today ✓`; secondary 48px `✎ Edit monster`, `aria-disabled="true"`, no handler (S4).

**Note on the bounty — one number, three renderings.** `coins` equals `recurrence_days`, doubled when starred. The row chip shows the sort key; the badge re-frames it as a reward and is the only element that reacts to `starred`; `RECURRENCE` states the scheduling fact. The duplication is deliberate — do not “fix” it by dropping one.

---

## 10. Screen 5 — Search (`search.html`)

### 10.1 Identity
The field is the page identity: no title, no subtitle. The trail states the active filter (§5.4); the pill row lists the alternatives at that level.

### 10.2 Entry points and the preselected filter

| Entered from | Trail | Pill level | Preselected | Pills shown |
|---|---|---|---|---|
| Home | `Recurrator / All / Search` | scope | `All` | `Work · Personal · Both` |
| Scope `Work` | `Recurrator / Work / Search` | scope | `Work` | `All · Personal · Both` |
| Context `telefono` | `Recurrator / <Scope> / telefono / Search` (All in the mockup) | context | `telefono` | the other 15 contexts |

Home and the `All` scope are the identical entry — `Recurrator/All` in both cases. **The active value never appears as a pill**; the trail is already saying it.

### 10.3 Sticky region
`position:sticky; top:0` on the trail **and** the field only (~110px). The pill block, the count row and the divider scroll away. The sticky region is opaque (`--c-bg-page` at full alpha) and gains a hairline at its lower edge only once content is behind it; rows never show through the gap.

### 10.4 The field
48px, pill radius, `--c-surface`, hairline border, 16px text, 18px magnifier, clear button 44×44 (`aria-label="Clear search"`). `type="search" inputmode="search" enterkeyhint="search" autocapitalize="none" autocomplete="off" spellcheck="false"`.

### 10.5 The pill row
- Items are the alternatives at the current level, **minus the active value**. There is no reset pill and no `×`.
- **Wraps to multiple rows** (no horizontal scroll), in fixed display order: scopes `All, Work, Personal, Both`; contexts alphabetical.
- Pill 32px, `--c-surface` at rest, label 12px/600 centered, `--c-muted`.
- **Pill width = measured label width + 24, and that same measurement sets the row advance.** Measure once, use twice: it is the invariant that stops a label overflowing its pill. `doctoradoadmin` is the case that exposes a violation.
- Gap **8px inline and 8px block**; wrap when `x + w` exceeds the current content width (373 at the 393 reference, 380 at the 420 cap).
- Each pill is a `<button>` that **replaces** the active filter at its level and keeps the query, the sort and the other levels. Because the active value is never in the row, pills have no selected state in the shipped app — the styleguide defines one anyway.
- Level changes when a filter is cleared (§5.4): the row re-renders in place, scroll position 0.

### 10.6 The count row
`<n> tasks` (`--c-ink`) at the left; on the right the sort control **`Sort ⇅`** (11–12px, `--c-muted`). While summaries stream in: `Loading 37 of 223…`, then the real count. There is **no overdue count**. Tapping `Sort ⇅` inverts `due_date` ordering; the glyph flips (`⇅` ascending, `⇵` descending). The count row scrolls away with the content — sorting is a start-of-visit action.

### 10.7 Rows
Reuse `ui.renderTaskRow` (§8) with the meta line:

```
[thumb]  Llamar Felipón.                                   ● 177
         📞 telefono · Overdue 4 months
```

- Meta = `[emoji] context · status`. The emoji comes from `ui.contextMeta(name)` and is `aria-hidden`; its advance is fixed (`1.15em + 4px`) so the line doesn't jitter across platforms.
- **The context is always shown**, even when the filter is a single context.
- **Truncation order:** the context truncates, the status never does. `telefo… · Overdue 4 months` is correct; `telefono · Overdu…` is a bug.
- State colour appears only in the status dot and the status text; no frames on rows.
- One height only. No snippet, no highlight.

### 10.8 Sort and matching
- `due_date` ascending by default, overdue first, undated last, ties by `coins` descending. ISO strings compare correctly — no date parsing anywhere.
- Tapping `Sort ⇅` inverts to descending (undated still last).
- Match rule: the query is matched **inside `description` only**, case- and diacritic-insensitive (`NFD` + strip marks, lowercase both sides), all terms must appear (AND). No weights, no title field, no context field.
- Because `monsterTitle` is the first three words of the description, every title match is also a description match — nothing is lost by having one field.
- Context names are **not** matched: contexts are filters (§10.5).

### 10.9 States
- **Loading:** the frame renders immediately (trail, field, pills, count row), then 6 skeleton rows. The field is focusable and typeable from the first paint; typing filters whatever has already arrived.
- **Empty query:** the same page, the whole (filtered) catalogue, no special case.
- **No results:** ghost monster (10% ink), then `No monsters match “karla” in 📞 telefono` (15/700), then **one full-width secondary button**: **`Clear all`**, which navigates to bare `search.html` with no query and no filters. The block is an `h2` plus the button inside a container with `aria-live="polite"`; `role="status"` stays on the count row only.
- **Error:** retry card that keeps the query and the filter.

### 10.10 URL state
`search.html?query=karla&context=telefono&sort=desc&scope=all`. Supported keys: `query` (string), `context` (context name), `scope` (`all|work|personal|both`), `sort` (`asc|desc`). Writing is `history.replaceState` on a 200ms debounce. **No scroll restoration**: the page does not save or restore `scrollTop`; the browser’s native behavior is accepted.

### 10.11 Data and performance
- **Fallback (today):** `GET /task/` → `summaries(ids)` → browser matches, filters and sorts. Scope filtering uses the context lists cached from the scope views (§2.4).
- **Target (`D6`):** `GET /search/?query={string}` returns the matching full task objects. The browser still applies the context/scope pills and the Sort control; the server matches the description only. The cached scope lists still map each context to its scope.
- 223 rows, no virtualisation. First open costs `1 + 223` requests at pool 6; the session cache makes the second visit instant. Revisit above ~500 tasks.

---

## 11. Behaviour rules

### 11.1 Accent hashing
```js
const ACCENTS = ['orange','yellow','green','aqua','blue','purple','red'];
function accentFor(name){ let s=0; for (const ch of name.toLowerCase().trim()) s+=ch.charCodeAt(0); return ACCENTS[s%7]; }
```
`activity` → 877 → `green`. Deterministic, no storage. Adjacent collisions are accepted.

### 11.2 Title from description
Strip markdown and leading list markers → first 3 words of the first non-empty line → capitalise the first letter. No ellipsis. Fewer words → use all.

### 11.3 Markdown subset
Paragraphs, `**bold**`, `_italic_`, `` `code` ``, `- ` lists, `- [ ]`/`- [x]` checks, `[text](url)`, line breaks; everything else literal.
- Escape HTML before transforming. Descriptions are user data.
- Decode the CSV line-break escape first: the data stores a break as the characters backslash and n; one escape breaks a line inside a paragraph, two separate paragraphs.
- Links `target="_blank" rel="noopener noreferrer"`.
- Checks: real checkbox, `accent-color: var(--c-orange)`, toggling local-only (S5).

### 11.4 Due state
```js
due_date <= getTodayISO() → 'due'     (--state-due)
due_date >  getTodayISO() → 'not-due' (--state-not-due)
```
Basis `America/Los_Angeles`. No severity tiers. No due date → no frame (styleguide-only defensive state).

### 11.5 Status line copy
| Condition | Text | Colour |
|---|---|---|
| done today / yesterday | `Done today` / `Done yesterday` | `--state-not-due` |
| `due_date` < today | `Overdue by 3 days` (<30), `Overdue by 3 months` (≥30) | `--state-due` |
| `due_date` == today | `Due today` | `--state-due` |
| future | `Due in 12 days` (≤45), else `Due in 3 months` | `--c-muted` |

Months are `floor(days/30)`, pluralised. The “done” line uses `latest_done_date` when `D5` exists; until then it uses `latest_date` and inherits the known skip-date discrepancy. The stat-grid dates stay ISO.

### 11.6 Done flow
`POST /task/{id}/done` → 2xx: drop the id from the summary cache, re-fetch the task, re-render in place.
**409** (already done today or yesterday): drop the cached id, re-fetch the task, re-render it, and show `Already marked done.` with the button disabled. A 409 is a normal outcome, not an error.
Other failures: button returns to `✓ Mark as Done`, inline `Didn't save. Try again.`, raw error to `console.error`. The POST also nudges sibling ratings: do not cache card ratings across a done.

---

## 12. Accessibility

- Every target ≥ 44×44. Trail ancestors fill the 44px row.
- `aria-current="page"` on the current oval; ancestors that navigate are links; the inert context oval is a `span` with no role; the widening oval is a `button`.
- Search: field has a label; pills are buttons (state is implied by absence + trail, so `aria-pressed` is not used — announce instead `Show only <label>`); count row is `role="status"` with `aria-live="polite"`, debounced to announce on settle.
- Emoji in the meta line and in the no-results headline: `aria-hidden` on the decorative copy where the text already says it; the headline's emoji is decorative, the context name carries the meaning.
- Star badge `aria-label="Starred"/"Not starred"`, not a button. Rating badge: hidden `Rating` prefix.
- Decorative discs, dots, chevrons: `aria-hidden="true"`.
- Contrast, verified: `--c-ink`/`--c-surface` 8.6:1 · `--c-muted`/`--c-surface` 5.0:1 · 11px labels use `--c-muted` only.
- Focus visible: 2px `--c-blue`, offset 2px.
- `prefers-reduced-motion`: colour-only transitions.
- No colour-only information: state is always also text.

---

## 13. Stub and dependency register

### 13.1 Scope map — from `~/.config/recurrator/context.csv`

| Scope | Contexts |
|---|---|
| Work | `admingeci`, `bycatchcode`, `doctoradoadmin`, `gecicode`, `lider` |
| Personal | `actividad`, `casa`, `chores`, `electronica`, `laptop`, `lectura`, `mandado`, `telefono` |
| Both | `escritura`, `estudio`, `tresminutos` |

`Both` means *neither scope, or both* — a bucket, not an intersection. It lives in `ui.js: CONTEXT_META` beside the emoji, for labels and trails. The scope views in §2.4 supply the same grouping to every list, so this table is display metadata and the browser tests' fixture, not a second source for filtering. The mockup’s `Work 5 / Personal 7 / Both 3 / All 15` is consistent with this map when one Personal context is not due that day.

### 13.2 Stubs

| # | Stub | Where | Replace with |
|---|---|---|---|
| S2 | One placeholder PNG for every monster | `ui.js` | sprite/art lookup |
| S3 | Bounty badge displays, never toggles | `ui.renderMonsterCard` | `D2` |
| S4 | `Edit monster` disabled, no handler | `ui.renderMonsterCard` | `edit.html` + `D4` |
| S5 | Checks toggle in memory only | `ui.renderMarkdown` | `D4` |
| S6 | Context emoji hardcoded; the roster and scope grouping come from the scope views | `ui.js: CONTEXT_META` | an emoji field, if the API ever has one |
| S8 | Search matching is client-side over the cached catalogue; the browser still filters and sorts after `D6` | `main.js` | `D6` — the server matches the description |

`S1` retired: the scope views filter the lists and supply the grouping; see Appendix A. `S7` retired: the summariser keeps one request per task, because no bulk route is planned.

### 13.3 Dependencies

| # | Needed | Blocks | Minimal assumed shape |
|---|---|---|---|
| D2 | Star toggle | S3 | `PATCH /task/{id}` with `starred` |
| D4 | Description write | S4, S5 | `PATCH /task/{id}` with `description` |
| D5 | Last completion date | `LATEST DONE` and the done status | `latest_done_date` (`date_4`) in `GET /task/{id}` |
| D6 | Server-side text search | S8 | `GET /search/?query={string}` → full task objects (including `context` and `due_date`); description match only |

The former `D1` (a scope field on tasks and contexts) is retired: the scope views in §2.4 supply the grouping. The former `D3` (bulk task summaries) is retired as well: the summariser keeps one request per task.

**D6 detail.** The endpoint matches `query` in `description`, case- and diacritic-insensitively, and returns the same task fields as `GET /task/{id}`. The browser applies the context/scope pills and the Sort control; the endpoint does not accept those parameters. Use the canonical trailing-slash route `/search/`; do not rely on FastAPI's slash redirect.

**D5 detail.** The target value is the stored fourth completion date, not the skip-adjusted `latest_date`. The backend already computes it as `Task.latest_done_date`; the change is serialization. Until it lands, `LATEST DONE` displays `latest_date` and a skipped task may show a skip date.

Each dependency has a working fallback. None of them justifies a blank screen or an invisible button.

---

## 14. Styleguide (`styleguide.html`, unlinked)

1. Token swatches: page/background surfaces, `--c-cream`, ink/muted/faint, 7 accents, state colours.
2. Every type style at its size: 25, 23, 16, 15, 14, 12, 11.
3. Home tile — normal, zero-due.
4. Context card — short, `doctoradoadmin`, each accent.
5. Task row — short, long/truncated, with bounty, with the emoji meta line.
6. Monster card — not-due/unstarred, due/starred, overdue/starred, no-due-date; `LATEST DONE` label.
7. Markdown — seven constructs plus `\n` and `\n\n` decoded.
8. Buttons — primary, saving, done, 409, secondary-disabled.
9. Skeleton, empty (celebratory), error, **no-results**.
10. Trail — home, scope, context, card, search (both 3-level and 4-level); ancestor vs current vs **inert** vs **widening button**; `Personal` + `doctoradoadmin` + `#999`; collapsed `…` variant.
11. Filter pills — scope set, context set, **wrapped to 4 rows**, and the selected-looking state the styleguide must still define even though the app never shows it.

---

## 15. Definition of done

1. Five screens render at the 393px capture reference with no horizontal scroll and nothing clipped; the layout is fluid to the 420px cap.
2. Headers follow §5.1; the magnifier appears on home/scope/context and never on card or search.
3. On `search.html`: the active filter is **absent** from the pill row; the scope oval widens; the context oval is inert; no `×` anywhere.
4. `grep -E "#[0-9a-fA-F]{3,6}" styles/components.css styles/pages.css` → no results.
5. The token file contains only the §4 closed set; no new colour or derived tokens were added.
6. No network requests except the API.
7. **No call to `/context/{id}/due/{date}` originates from `search.html`.**
8. The task list renders in API order, unsorted client-side.
9. Search: `?query=karla&context=telefono` survives a reload; Back does **not** restore scroll position; the result bar announces once per settle.
10. Row meta truncates the context, never the status.
11. Every state in §14 is visually verified, including pills wrapped to 4 rows; search states are verified when its capture matrix is added.
12. Targets ≥44px, contrast checked, focus visible.
13. `main.js` may add initialisers and data flow; no rendering logic in it.
14. `<meta name="viewport">` in all five shells; Pico `<link>` gone.
15. Each home tile's count equals the length of its scope view, and the four counts sum to the `All` count.
16. No pill label ever overflows its pill at any filter level — `doctoradoadmin` is the test case.
17. The current oval fills the row up to the magnifier's reserved edge, ancestors are content-sized, and no oval wraps.
18. The celebratory empty state is the same component and copy on both lists, with no back link.
19. `LATEST DONE` displays `latest_done_date` once `D5` exists; until then the fallback and the known discrepancy are documented in §13.3.

---

## 16. Open items

| # | Question | Current default |
|---|---|---|
| O1 | Retry: `location.reload()` or re-run init? | `location.reload()` |
| O2 | Files flat in `public/` or nested? | flat, except `styles/` |
| O3 | Home tile at 0 due: `Victorious` or `Nothing due`? | `Victorious` |
| O4 | Empty lists: message only? | one celebratory state, message only |
| O5 | Bounty on the row *and* the card badge? | yes — row shows the sort key, card the reward |
| O6 | Description clamp 4 lines, no expander? | yes |
| O7 | Context emoji: fixed map or generic? | fixed map (`S6`) |
| O8 | Cannot narrow to a context from scope level | accepted; **fallback** if it bites: a `Scopes ⇄ Contexts` level switch at the head of the pill row, no layout change |
| O9 | `Sort` scrolls away with the count row | accepted at 223 tasks; revisit if it becomes a top action |
| O10 | No-results `Clear all` widens to bare `search.html` | accepted — the empty state offers the maximal widening, the trail offers the minimal one |
| O11 | Scope map in §13.1 | settled from `context.csv`; the scope views are the runtime source |
| O12 | `D6` route uses a trailing slash | settled: `/search/?query={string}` |
| O13 | Search captures and browser tests | next frontend loop; the four existing screens remain the approved baseline |
| O14 | The path-based routes are documented but not yet served | the frontend switches calls when they land; §2.4 names the one place |

---

## Appendix A — Superseded rules

| Previous rule | Merged rule |
|---|---|
| “The backend is frozen; use only existing fields.” | API is a dependency; `D2`, `D4`, `D5` and `D6` with fallbacks. |
| Four screens. | Five screens, including search. |
| Breadcrumb: 12 units, 24px ovals, 10px task oval. | Content-sized ancestors, 32px ovals, 11px task oval, magnifier reserve, `…` collapse. |
| Only the `All` tile counts and previews. | All four tiles count and preview through their scope views; the scope list filters through the same views. |
| Task list sorted by `coins` descending. | `/context/{id}/due/{date}` order, untouched; no client sort. |
| The context collection returned only due contexts, and `?date=` narrowed it. | The collection returns the full roster; the date lives in the path and the due views carry it. |
| The context detail always wrote skip data. | The bare detail is a read-only roster; only the dated due view writes. |
| Scope filtering depended on a scope field (`D1`). | The scope views supply the grouping; the field dependency is retired. |
| Bulk task summaries (`D3`). | The summariser keeps one request per task; no bulk route is planned. |
| `LATEST DONE` shows the current value with no caveat. | `LATEST DONE` stays; `D5` requests `latest_done_date`; fallback documented. |
| Any non-2xx completion is a generic failure. | 409 is a normal outcome; re-fetch and show the actual state. |
| No search. | Search screen, `D6` query-only endpoint, client fallback, URL state, sticky header, one “Clear all”. |
| Search row showed `<n> tasks · <m> overdue` in the mockup. | `<n> tasks` only. |
| 21 colour tokens and 9 type sizes. | Closed role-based set: no `--c-bg-3`, `--c-bg-4`, `--c-ink-2`; `--c-cream`; seven type sizes. |
| Width contract 393/320/443 variants. | One `max-width: 420px`; 393px capture reference only. |
| v3.2 scope map (15 contexts). | Actual `context.csv` map: Work 5, Personal 8, Both 3. |
| Empty task list “No monsters left here.” + back link. | One celebratory state reused on both lists, no back link. |
