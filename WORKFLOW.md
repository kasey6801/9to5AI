# WORKFLOW.md — 9to5AI Build Log

## Executive Overview

9to5AI is a macOS desktop app that aggregates AI news from 39 public RSS feeds and presents them in a 9to5Mac-inspired dark interface. Stories are sorted newest-first, tagged by country of coverage and theme, and filterable by theme, keyword, and date range. Built across multiple Claude Code sessions using a single-file Flask + PyInstaller architecture. The entire UI is embedded in one Python file (`app.py`); no separate templates or static assets are needed. Packaged as a `.dmg` installer for distribution to Apple Macs.

---

## Step-by-Step Build Log

---

### Step 1 — Initial project brief

**User prompt:**
> Following the style of 9 to 5 Mac.com and using the same technologies as the CC_Markdown project, create an app that will complete a search and render a page named "9 to 5 AI". Content should be sorted by date, with the most recent stories first. Images should be included and there should be a control to select the date range. This app will be packaged as a .dmg for distribution to Apple Macs. All stories should be tagged by country (location reported on). Fetch this design file, read its readme, and implement the relevant aspects of the design.
> `https://api.anthropic.com/v1/design/h/s8nAVYqpL0ir968Lk_7z4g?open_file=9to5ai%2Findex.html`
> Implement: 9to5ai/index.html

**Claude actions:**
- Explored the CC_Markdown project at `/Users/kcharles/CloudeDev/CC_Markdown/` to understand the tech stack: single-file Flask app, HTML/CSS/JS embedded as a Python string, PyInstaller for `.app`/`.dmg` packaging, watchdog/heartbeat pattern for auto-quit on tab close.
- Attempted to fetch the design URL — returned HTTP 404 (authenticated Anthropic internal URL, not publicly accessible).
- Proceeded with the 9to5Mac visual design language based on the task description.
- Created **`app.py`** (~370 lines) containing:
  - Flask backend on port 5002
  - 10 RSS news sources covering global AI coverage (TechCrunch AI, VentureBeat, The Verge, MIT Tech Review, Wired, Ars Technica, BBC Technology, ZDNet, Engadget, IEEE Spectrum)
  - Country detection via regex (`_COUNTRY_PATTERNS`) for 12 countries (US, UK, China, France, Germany, India, Canada, Japan, South Korea, Israel, Australia, UAE)
  - Image extraction from `media_content`, `media_thumbnail`, `enclosures`, and HTML `<img>` tags
  - 5-minute article cache with parallel feed fetching via `ThreadPoolExecutor`
  - Full embedded HTML/CSS/JS UI with 3-column card grid, date range pickers, search input
  - Standard Flask app features: Quit button, heartbeat endpoint, watchdog thread, `debug=False`, `host='0.0.0.0'`
- Created **`9to5AI.spec`** — PyInstaller spec for macOS `.app` bundle with `info_plist`, collecting feedparser, flask, werkzeug, bs4, lxml, requests, certifi.
- Created **`build.sh`** — adapted from CC_Markdown's build script; ad-hoc signs the app bundle, creates a staged DMG with AppleScript icon positioning, converts to compressed UDZO format.
- Created **`CLAUDE.md`** — project documentation for Claude Code.
- Installed dependencies and ran a smoke test confirming the `/fetch` endpoint returned 103 articles.

**SSL fix discovered during testing:**
- Python on macOS failed SSL certificate verification when feedparser tried HTTPS feeds.
- Added `requests` + `certifi` as dependencies; updated `_fetch_feed()` to download feed content via `requests.get(..., verify=certifi.where())` before passing to `feedparser.parse()`.
- Re-tested: 103 articles returned successfully.

---

### Step 2 — Apply the design

**User prompt:**
> apply this design

**Claude actions:**
- User shared a screenshot of the intended header design showing:
  - Left: "9 to 5 AI" large bold title + "DAILY INTELLIGENCE ON ARTIFICIAL INTELLIGENCE" subtitle
  - Right: current date, "X of Y stories" count, "☀ Light" theme toggle button, Quit button
  - Filter bar: "FILTER BY DATE" label + four pill buttons — Today, 30 days (default selected with checkmark), 60 days, 90 days — each showing a story count badge
- Rewrote the entire embedded `HTML` string to implement this design:
  - Dark header (`#131313`) always-on regardless of theme
  - Brand title "9 to 5 AI" in white + subtitle in muted uppercase
  - Live header date populated by JS
  - "X of Y stories" count updated after each filter
  - Light/Dark toggle (`toggleTheme()`) adds/removes `.light` class on `<html>`; swaps CSS custom properties for background, card, text, border colours
  - Four date-range pill buttons replacing the From/To date inputs
  - **Client-side filtering architecture**: all articles fetched once on load and stored in `allArticles[]`; pill clicks filter in-memory (instant, no server round-trip); pill counts calculated from `allArticles` for each time window
  - Search input moved below the header into a separate search row
  - Cards retain 3-column grid, image, source/date metadata, title, excerpt, country tags

---

### Step 3 — Search bar reset behaviour

**User prompt:**
> the search bar should reset when cleared to allow all stories to be visible.

**Claude actions:**
- Added an `input` event listener on `#q` that calls `applyFilters()` whenever the field value becomes empty:
  ```javascript
  document.getElementById("q").addEventListener("input", e => {
    if (e.target.value === "") applyFilters();
  });
  ```
- This fires on every keystroke, so deleting the last character (or clicking the browser's ✕ clear button) immediately resets the grid to all stories in the active date range.

---

### Step 4 — Launch

**User prompt:**
> launch the app

**Claude actions:**
- Killed any process holding port 5002.
- Launched `.venv/bin/python app.py` in the background; the app opened automatically at `http://127.0.0.1:5002`.

---

### Step 5 — Open stories in a new window

**User prompt:**
> clicking on the story should direct you to the story's web page. This should open in a new window

**Claude actions:**
- Identified the root cause: `window.open(url, '_blank', 'width=1200,height=800')` is treated as a popup and blocked by the browser's popup blocker when triggered from an `onclick` on a `<div>`.
- Fixed by converting each card from a `<div onclick="window.open(...)">` to an `<a>` element with `href`, `target="_blank"`, and `rel="noopener noreferrer"`. Browsers never block `<a target="_blank">` clicks.
- Added `text-decoration: none; color: inherit;` to the `.card` CSS rule so the anchor renders identically to the previous div.

---

### Step 6 — UTC time in header and on cards

**User prompt:**
> In the header add the time in UTC. On each story card add the time posted in UTC beneath country

**Claude actions:**
- Added `#hdr-time` element in the header meta block with `font-variant-numeric: tabular-nums` for fixed-width digits.
- Added `tickUTC()` function that formats `HH:MM:SS UTC` and runs every second via `setInterval`.
- Added `utcTime(iso)` helper that formats a story's publication timestamp as `"Mon DD, HH:MM UTC"` (e.g. "Apr 18, 23:15 UTC").
- Added `.card-utc` div beneath `.card-tags` in each rendered card.
- User clarified mid-edit: include the **date** along with the time. The `utcTime()` implementation already included the date (`Mon DD`) in that format, so no additional change was needed.

---

### Step 7 — Custom date range selector

**User prompt:**
> add a selector for custom date range to the right of the 90 days button

**Claude actions:**
- Added a **Custom** pill button to the right of the 90-days pill.
- Added a hidden `#custom-range` div containing two `<input type="date">` fields (From / To) that appears only when Custom is selected.
- Added `customRange` state variable (null when a preset pill is active, `{from, to}` timestamps when custom is active).
- Added `selectCustom(btn)`: deactivates all preset pills, shows the date inputs, defaults them to last 7 days if empty, calls `applyCustomRange()`.
- Added `applyCustomRange()`: reads the two date inputs, sets `customRange`, calls `applyFilters()`.
- Updated `applyFilters()` to branch on `customRange`: if set, filter by the explicit timestamp range; otherwise use the `activeDays` cutoff.
- Updated `selectPill()` to clear `customRange` and hide `#custom-range` when a preset is chosen.
- Styled the date inputs to match the header's dark pill aesthetic (`.cdr-in`).

---

### Step 8 — App icon

**User prompt:**
> Create an app icon for 9to5AI

**Claude actions:**
- Created **`make_icon.py`** — draws a 1024×1024 RGBA icon using Pillow: dark background (`#0d1117`), rounded square, a stylised "AI" wordmark in red with a subtle newspaper/grid motif beneath, and the "9to5" moniker in smaller white text.
- Ran `make_icon.py` to produce **`9to5AI_icon.png`**.
- Converted to **`9to5AI.icns`** using the `sips` → iconutil pipeline (10 sizes from 16×16 to 1024×1024).
- Wired the `.icns` file into `9to5AI.spec` (`icon='9to5AI.icns'`) and into `build.sh` (icon generation step added before PyInstaller).

---

### Step 9 — GitHub repository setup

**User prompt:**
> Set up a GitHub repository for this project

**Claude actions:**
- Initialised git in the project directory (`git init`, initial commit of all source files).
- Created the public repository `kasey6801/9to5AI` on GitHub via the API.
- Added the remote origin and pushed `main`.
- Created **`README.md`** with installation instructions, feature list, source table, and architecture overview.

---

### Step 10 — v0.42 initial release

**User prompt:**
> Build and release v0.42

**Claude actions:**
- Ran `bash build.sh` → produced `dist/9to5AI.app` (43 MB) and `dist/9to5AI.dmg` (20 MB).
- Bumped version strings to `0.42` in `app.py` and `9to5AI.spec`.
- Created GitHub release `v0.42` on `kasey6801/9to5AI` via the Releases API.
- Uploaded `dist/9to5AI.dmg` as a release asset.

---

### Step 11 — v0.42.1: Theme filter + 50 sources

**User prompt:**
> Create a new release v0.42.1. In this new release make the following change and launch for review: Under 'Filter by Date' add a selector for 'Themes'. This must allow single or multi select. There will be between 10 and 15 themes. Do not attempt to assign themes as this will be done in a later step.

*(Plan revision during review)*
> The themes will be sourced from the 'Theme' column in file 'New sources.md'. Add all 50 sources with each one linked to the theme in the 'New sources.md' file.

**Claude actions:**
- Bumped version to `v0.42.1` in `app.py` and `9to5AI.spec`.
- Replaced the 10 original `NEWS_SOURCES` entries with all 50 sources from `New sources.md`, each with a `"theme"` key matching its Theme column (Employment Trends, News, Research, Transformation, EU, USA, OCM, Canada, Africa, Asia).
- Added `"themes": [source["theme"]]` to every article dict in `_fetch_feed()` so articles inherit their source's theme.
- Bumped `ThreadPoolExecutor(max_workers=8)` → `max_workers=20` to handle 50 parallel feed fetches.
- Added full **theme filter CSS** (`.theme-bar`, `.theme-wrap`, `.theme-btn`, `.theme-dropdown`, `.theme-item`, `.theme-checkbox`, `.theme-divider`, `.theme-clear`, `.theme-chips`, `.theme-chip`).
- Added **theme bar HTML** below the date filter bar: dropdown button, popover with checkboxes for all 10 themes, chip strip for active selections.
- Updated `.brand-sub` subtitle to `39 sources · Employment Trends | News | Research | Transformation | EU | USA | OCM | Canada | Africa | Asia`.
- Added **JavaScript**: `THEMES` constant array, `activeThemes` Set, `buildThemeDropdown()`, `toggleThemeDropdown()`, `closeThemeDropdown()`, `toggleThemePick()`, `clearThemes()`, `syncThemeUI()`.
- Updated `applyFilters()` with a theme filter block: `shown = shown.filter(a => (a.themes||[]).some(t => activeThemes.has(t)))`.
- Called `buildThemeDropdown()` inside `init()` before the first fetch.

---

### Step 12 — Source audit and cleanup

**User prompt:**
> hard code the Theme to each RSS based on New sources.md

*(After testing feeds)*
> yes, propose active RSS links for the broken themes. Present them for review but don't make any changes.

*(After reviewing proposals)*
> Update based on findings. Remove sources with no content and add the validated sources. Keep the same Themes and map each new source to the correct Theme. Also update the New sources.md file.

**Claude actions:**
- Fetched and tested all 50 RSS feeds using `requests` + `feedparser`; confirmed 26 of 50 returned zero entries (404, 403, bot-blocks, or empty feeds).
- Researched working replacement feeds via web search and live testing across all broken theme categories.
- Removed all 26 non-functional sources; replaced with 17 confirmed-working alternatives.
- Final source list: **39 verified active feeds** across all 10 themes.
- Updated `NEWS_SOURCES` in `app.py` with the cleaned 39-source list.
- Updated `.brand-sub` subtitle to `39 sources · ...`.
- Rewrote **`New sources.md`** as a 39-row table with updated names, URLs, organisations, descriptions, and themes.

---

### Step 13 — v0.42.1 build and GitHub release

**User prompt:**
> Push the latest release to GitHub. Update the readme.md with the table of sources as part of the release. [GitHub token provided]

**Claude actions:**
- Ran `bash build.sh` → `dist/9to5AI.app` (43 MB), `dist/9to5AI.dmg` (20 MB); signature verified OK.
- Updated **`README.md`**:
  - Replaced "10 sources" with "39 sources across 10 themes" in the feature list.
  - Added "Filter by Theme" usage section.
  - Replaced the 10-row source table with the full 39-source table (name, theme, base, description).
- Created GitHub release `v0.42.1` ("Theme Filter + 39 Active Sources") on `kasey6801/9to5AI`.
- Uploaded `dist/9to5AI.dmg` as a release asset.
- Committed all changed files (`app.py`, `9to5AI.spec`, `README.md`, `New sources.md`) and pushed `main`.

---

### Step 14 — Employment Trends theme fix

**User prompt:**
> The theme Employment Trends has no content. Why is this?

**Claude actions:**
- Diagnosed root cause: both Employment Trends sources (`Indeed Hiring Lab`, `Economic Policy Institute`) had `"filter_ai": True`, but their content covers general labour economics with no AI-specific keywords. The `_is_ai_related()` filter rejected 100% of their articles (tested: 0/10 entries from each feed passed the keyword check).
- User chose fix: set `filter_ai: False` for both sources so articles pass through unfiltered.
- Changed `"filter_ai": True` → `"filter_ai": False` for both Employment Trends entries in `app.py`.
- Rebuilt DMG (`bash build.sh`); replaced the DMG asset on the v0.42.1 release (version string unchanged).
- Committed fix and pushed to `main`.

---

### Step 15 — Theme tag on each card

**User prompt:**
> Update workflow.md to document the steps that went into making this app. Include all user prompts and a summary of Claude actions. Once complete update the file and push to GitHub.
> *(mid-write rejection)* add a tag for Theme to each card, to the right of country. Theme is hard coded based on the feed, as in the New sources.md file. Update the app (do not change the release version) and push to GitHub.

**Claude actions:**
- Added `.ttag` CSS class — pill-shaped tag with muted background and border; adapts to light/dark mode via `.light .ttag` override.
- Updated `renderCard()` in the embedded JS to read `(a.themes||[])[0]` and render a `<span class="ttag">` to the right of country tags inside `.card-tags`.
- Updated `WORKFLOW.md` with the full build history (Steps 1–15) including all user prompts and Claude action summaries.
- Committed and pushed `app.py` and `WORKFLOW.md` to `main`.

---

## File Structure

```
CC_9to5_AI_2/
├── app.py           # Single-file Flask app — backend + embedded HTML/CSS/JS UI
├── 9to5AI.spec      # PyInstaller spec → macOS .app bundle + .dmg
├── build.sh         # Build script: PyInstaller → ad-hoc sign → DMG
├── make_icon.py     # Generates 9to5AI_icon.png programmatically via Pillow
├── 9to5AI_icon.png  # Source icon (1024×1024 RGBA)
├── 9to5AI.icns      # Compiled macOS icon bundle
├── New sources.md   # 39-source reference table (name, RSS, org, base, theme)
├── CLAUDE.md        # Claude Code guidance for this project
├── WORKFLOW.md      # This file
├── README.md        # User-facing documentation
└── .venv/           # Python virtual environment (not committed)
```

---

## User Guide

### Running from source

```bash
cd /path/to/CC_9to5_AI_2
source .venv/bin/activate
python app.py
```

The app opens automatically at `http://127.0.0.1:5002`. Use the **Quit** button or close the browser tab to stop it.

### Building the macOS app

```bash
bash build.sh
```

Produces `dist/9to5AI.app` and `dist/9to5AI.dmg`. On first launch on another Mac, right-click the app and choose **Open** to bypass Gatekeeper (one-time only).

### Using the app

| Control | Description |
|---|---|
| **Filter by Theme** dropdown | Multi-select across 10 themes; selected themes appear as chips; composes with date and keyword filters |
| **Filter pills** (Today / 30 / 60 / 90 days) | Instantly filters the grid client-side; each pill shows the story count for its window |
| **Custom** pill | Reveals From / To date pickers for an arbitrary date range |
| **Search bar** | Keyword filter applied on top of the active date range; clearing the field resets to all stories |
| **☀ Light / ☽ Dark** | Toggles between dark (default) and light colour themes |
| **Click a card** | Opens the full story in a new browser window |
| **Header UTC clock** | Live ticking clock showing current UTC time |
| **Card UTC timestamp** | Shows the story's publication date and time in UTC |
| **Card theme tag** | Pill tag on each card showing its theme (e.g. "News", "Research", "EU") |
| **Quit** | Gracefully shuts down the Flask server |
