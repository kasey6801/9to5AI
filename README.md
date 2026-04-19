# 9to5AI — AI News Aggregator

A macOS desktop app that aggregates AI news from around the world, presented in a **9to5Mac-inspired interface**. Stories are sorted by date (newest first), tagged by country of coverage, and filterable by keyword and date range. No API keys required — all content comes from public RSS feeds.

---

## Features

- **AI news from 39 sources across 10 themes** — Employment Trends, News, Research, Transformation, EU, USA, OCM, Canada, Africa, Asia
- **Theme filter** — multi-select dropdown with chip display; composes with date and keyword filters
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

### Filter by theme
Click **Filter by Theme** in the header to open a dropdown with all 10 theme categories. Select one or more themes — articles from unselected themes are hidden immediately. Selected themes appear as chips below the dropdown; click a chip (or **Clear all**) to deselect. Theme filters compose with date and keyword filters.

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

39 verified active feeds across 10 themes.

| # | Name | Theme | Base | Description |
|---|------|-------|------|-------------|
| 1 | Indeed Hiring Lab | Employment Trends | USA | Labor market research and AI‑related hiring trends |
| 2 | Economic Policy Institute | Employment Trends | USA | Worker‑focused economic analysis including AI's impact on jobs |
| 3 | TechCrunch AI | News | USA | Startup funding, product launches, and AI news |
| 4 | VentureBeat AI | News | USA | Enterprise AI tools, industry analysis and use‑case deep dives |
| 5 | The Verge AI | News | USA | Consumer AI, ethics, and societal impact stories |
| 6 | MIT Tech Review | News | USA | Frontier AI research, policy and innovation coverage |
| 7 | Wired AI | News | USA | AI regulation, culture, and long‑form tech features |
| 8 | Ars Technica AI | News | USA | Technical deep dives on models, infra, and tooling |
| 9 | BBC Technology | News | UK | Global tech and policy news including AI developments |
| 10 | ZDNet AI | News | USA | Enterprise IT + AI, product and deployment updates |
| 11 | Engadget | News | USA | Consumer AI gadgets and tech‑product launches |
| 12 | IEEE Spectrum AI | News | USA | Engineering standards, AI hardware, and systems |
| 13 | OpenAI News | Research | USA | Model releases, safety updates, and API changes |
| 14 | Google AI Blog | Research | USA | Research papers, MLOps, and infra‑level AI insights |
| 15 | Hugging Face Blog | Research | France | Open‑source tooling, models, and ecosystem tools |
| 16 | DeepMind Blog | Research | UK | Frontier research and safety‑oriented AI work |
| 17 | McKinsey Insights | Transformation | USA/Global | AI strategy frameworks, economic impact, and adoption paths |
| 18 | Deloitte Insights Podcast | Transformation | USA/Global | AI governance, risk‑management, and transformation frameworks |
| 19 | Change Management Review | Transformation | USA | Practitioner‑focused change management and AI adoption content |
| 20 | EU AI Act | EU | Belgium | AI Act enforcement, compliance timelines, and guidance |
| 21 | EC Digital Strategy | EU | Belgium | EU AI policy, digital‑strategy updates and roadmaps |
| 22 | Sifted AI/Europe | EU | UK | European AI startups, venture and ecosystem news |
| 23 | Euractiv EU Tech | EU | Belgium | EU tech‑policy analysis, including AI legislation |
| 24 | EDPS AI | EU | Belgium | Data‑privacy and AI‑compliance guidance in EU |
| 25 | NIST Information Technology | USA | USA | Federal IT and AI standards, risk management updates |
| 26 | Nextgov | USA | USA | Federal technology and AI adoption across US agencies |
| 27 | Defense One | USA | USA | Defense technology, AI in national security and DoD programs |
| 28 | GovCIO Media AI | USA | USA | Agency‑level AI implementations and federal CIO perspectives |
| 29 | FedScoop AI | USA | USA | Agency‑level AI implementations and case studies |
| 30 | Kotter Inc. | OCM | USA | 8‑step change leadership and AI‑driven org transformation |
| 31 | MIT Sloan Management Review | OCM | USA | AI strategy, workforce transformation, and management research |
| 32 | CD Howe Institute | Canada | Canada | Canadian economic policy including AI and digital economy |
| 33 | Open North | Canada | Canada | Open data, civic AI, and Canadian digital governance |
| 34 | Smart Africa AI | Africa | Rwanda | Continental‑level AI blueprint and African‑digital‑strategy |
| 35 | CIPESA AI Policy | Africa | South Africa | East‑Africa‑focused AI ethics and policy |
| 36 | Just Security | Africa | USA | National‑security, human‑rights, and AI governance coverage |
| 37 | CSET Georgetown | Asia | USA | US‑China tech competition, AI policy, and security research |
| 38 | Japan Digital Agency | Asia | Japan | Japan government AI strategy and digital‑government updates |
| 39 | Korea AI Times | Asia | South Korea | Korean AI industry news, startups, and policy updates |

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
