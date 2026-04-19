# 9to5AI — AI News Aggregator

A macOS desktop app that aggregates AI news from around the world, presented in a **9to5Mac-inspired interface**. Stories are sorted by date (newest first), tagged by country of coverage, and filterable by keyword and date range. No API keys required — all content comes from public RSS feeds.

---

## Features

- **AI news from 10 sources** — TechCrunch AI, VentureBeat, The Verge, MIT Technology Review, Wired, Ars Technica, BBC Technology, ZDNet, Engadget, IEEE Spectrum
- **Sorted newest first** — always
- **Country tags** — each story is tagged with the country it reports on (🇺🇸 🇬🇧 🇨🇳 🇫🇷 🇩🇪 🇮🇳 🇨🇦 🇯🇵 🇰🇷 🇮🇱 🇦🇺 🇦🇪)
- **Story images** — extracted from feed metadata; AI brain placeholder when unavailable
- **Date range filter** — preset pills (Today / 30 / 60 / 90 days) plus a custom date range picker
- **Keyword search** — filters within the active date range; clears automatically when field is emptied
- **UTC timestamps** — live UTC clock in the header; each card shows the story's publication date and time in UTC
- **Light / Dark mode** — toggle between themes; header always stays dark
- **Click to read** — opens the full story in a new browser window
- **5-minute cache** — feeds are refreshed in the background every 5 minutes
- **Self-contained** — no internet connection needed after feeds are cached; no API keys required
- **macOS .dmg installer** — distributable to any Mac running macOS 12 or later

---

## Screenshots

| Dark mode | Light mode |
|---|---|
| Dark header, card grid with country tags and UTC times | Same layout with light card backgrounds |

---

## Requirements

- macOS 12 (Monterey) or later
- Python 3.10 or higher (for running from source)
- Internet connection (to fetch RSS feeds)

---

## Installation

### Option A — DMG (recommended)

1. Download `9to5AI.dmg`
2. Open the DMG and drag **9to5AI.app** to your Applications folder
3. On first launch: **right-click → Open** to bypass Gatekeeper, then click **Open** in the dialog
4. The app opens in your default browser at `http://127.0.0.1:5002`

> **Note:** The right-click → Open step is a one-time Gatekeeper bypass required for apps without an Apple Developer ID. You will not be prompted again after the first launch.

### Option B — Run from source

```bash
# 1. Clone or download the project
cd /path/to/CC_9to5_AI_2

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install flask feedparser beautifulsoup4 lxml requests certifi

# 4. Run the app
python app.py
```

The app opens automatically at `http://127.0.0.1:5002`. Stop it with the **Quit** button or `Ctrl+C`.

---

## Building the DMG

Requires the virtual environment with PyInstaller installed:

```bash
source .venv/bin/activate
pip install pyinstaller
bash build.sh
```

Outputs:
- `dist/9to5AI.app` — the macOS application bundle
- `dist/9to5AI.dmg` — the distributable installer

---

## Usage

### Filter by date
Click the **Today**, **30 days**, **60 days**, or **90 days** pill buttons in the header. Each pill shows the number of stories available for that window. The grid updates instantly — no page reload.

For a specific date range, click **Custom** and use the From / To date pickers that appear to its right.

### Search
Type in the search bar and press **Enter** (or click **Search**) to filter stories by keyword within the active date range. Clear the field to return to all stories.

### Open a story
Click any card to open the full article in a new browser window.

### Toggle theme
Click **☀ Light** in the top-right to switch to light mode. Click **☽ Dark** to return to dark mode.

### Quit
Click the **Quit** button in the top-right corner. The Flask server shuts down and you can close the browser tab.

---

## News Sources

| Source | Coverage |
|---|---|
| TechCrunch AI | AI industry news |
| VentureBeat AI | AI business and research |
| The Verge AI | Consumer AI and tech |
| MIT Technology Review | AI research and policy |
| Wired AI | AI culture and technology |
| Ars Technica | Technology lab (AI-filtered) |
| BBC Technology | Global tech news (AI-filtered) |
| ZDNet AI | Enterprise AI |
| Engadget | Consumer tech (AI-filtered) |
| IEEE Spectrum AI | AI engineering and research |

---

## Country Detection

Stories are automatically tagged with countries detected from their title and summary text. Recognised countries:

| Flag | Country | Key signals |
|---|---|---|
| 🇺🇸 | United States | OpenAI, Anthropic, Google, Microsoft, Meta, NVIDIA, Silicon Valley |
| 🇬🇧 | United Kingdom | DeepMind, Arm, London, Britain |
| 🇨🇳 | China | Baidu, Alibaba, DeepSeek, ByteDance, Huawei |
| 🇫🇷 | France | Mistral, Hugging Face, Paris |
| 🇩🇪 | Germany | Aleph Alpha, Berlin |
| 🇮🇳 | India | Bengaluru, Mumbai, Infosys |
| 🇨🇦 | Canada | Cohere, Toronto, Montreal |
| 🇯🇵 | Japan | SoftBank, Sakana AI, Tokyo |
| 🇰🇷 | South Korea | Samsung, Naver, HyperCLOVA |
| 🇮🇱 | Israel | AI21, Tel Aviv |
| 🇦🇺 | Australia | Sydney, Melbourne |
| 🇦🇪 | UAE | G42, Falcon, Abu Dhabi |

---

## File Structure

```
CC_9to5_AI_2/
├── app.py          # Single-file Flask app — all backend + UI in one file
├── 9to5AI.spec     # PyInstaller spec for macOS .app/.dmg
├── build.sh        # Build script: PyInstaller → sign → DMG
├── CLAUDE.md       # Claude Code project guidance
├── WORKFLOW.md     # Full build log with every prompt and action
└── README.md       # This file
```

---

## Architecture

The app follows the same pattern as CC_Markdown:

- **Single Python file** (`app.py`) — no separate templates or static files
- **Entire HTML/CSS/JS UI** is embedded as a raw string (`HTML = r"""..."""`)
- **Flask** serves the UI and a `/fetch` JSON endpoint
- **feedparser + requests** fetch and parse RSS feeds; `beautifulsoup4` extracts images and clean text
- **5-minute in-memory cache** with parallel fetching (`ThreadPoolExecutor`)
- **Client-side filtering** — all articles loaded once, date/keyword filtering done in the browser
- **Watchdog thread** — monitors JS heartbeats; auto-exits if the browser tab is closed for > 12 s
- **PyInstaller** bundles everything into a self-contained `.app` with no external dependencies

---

## License

MIT
