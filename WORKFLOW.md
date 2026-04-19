# WORKFLOW.md — 9to5AI Build Log

## Executive Overview

9to5AI is a macOS desktop app that aggregates AI news from ten public RSS feeds and presents them in a 9to5Mac-inspired interface. It was built in a single Claude Code session using the same Flask + PyInstaller architecture as the CC_Markdown project. The entire UI is embedded in one Python file (`app.py`); no separate templates or static assets are needed. The app is packaged as a `.dmg` installer for distribution to Apple Macs.

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

## File Structure

```
CC_9to5_AI_2/
├── app.py          # Single-file Flask app — backend + embedded HTML/CSS/JS UI
├── 9to5AI.spec     # PyInstaller spec → macOS .app bundle + .dmg
├── build.sh        # Build script: PyInstaller → ad-hoc sign → DMG
├── CLAUDE.md       # Claude Code guidance for this project
├── WORKFLOW.md     # This file
├── README.md       # User-facing documentation
└── .venv/          # Python virtual environment (not committed)
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
| **Filter pills** (Today / 30 / 60 / 90 days) | Instantly filters the grid client-side; each pill shows the story count for its window |
| **Custom** pill | Reveals From / To date pickers for an arbitrary date range |
| **Search bar** | Keyword filter applied on top of the active date range; clearing the field resets to all stories |
| **☀ Light / ☽ Dark** | Toggles between dark (default) and light colour themes |
| **Click a card** | Opens the full story in a new browser window |
| **Header UTC clock** | Live ticking clock showing current UTC time |
| **Card UTC timestamp** | Shows the story's publication date and time in UTC |
| **Quit** | Gracefully shuts down the Flask server |
