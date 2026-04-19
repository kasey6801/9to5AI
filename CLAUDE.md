# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Running the app

```bash
source .venv/bin/activate
python app.py
```

Opens automatically at `http://127.0.0.1:5002`. Stop with the Quit button or `Ctrl+C`.

## One-time setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask feedparser beautifulsoup4 lxml pyinstaller
```

## Building

### macOS `.app` + `.dmg`
```bash
bash build.sh
```
Outputs `dist/9to5AI.app` and `dist/9to5AI.dmg`.

## Architecture

Single-file app (`app.py`, ~370 lines). No templates directory or separate static assets.

**Key design decisions:**

- **Entire HTML/CSS/JS UI** is embedded as the raw string `HTML` (search for `HTML = r"""`). When editing the frontend, work inside that string.
- **RSS aggregation** uses `feedparser` across 10 AI news sources with a 5-minute in-memory cache (`_cache`). Fetches run in parallel via `ThreadPoolExecutor`.
- **Country detection** uses regex patterns in `_COUNTRY_PATTERNS`. Add new countries or patterns there.
- **Image extraction** tries `media_content`, `media_thumbnail`, `enclosures`, then HTML `<img>` tags in the feed body.
- **Watchdog thread** (`_watchdog()`) monitors JS heartbeats (POST `/heartbeat` every 5 s). No heartbeat for 12 s → `os._exit(0)`.
- **`debug=False`** — required for PyInstaller bundles.
- **`host='0.0.0.0'`** — required on macOS Sequoia where `localhost` may resolve to `::1`.

**Flask routes:**

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the embedded HTML UI |
| `/fetch` | POST | Accepts `{"query","date_from","date_to"}`, returns JSON articles array |
| `/quit` | POST | Exits after 0.4 s delay |
| `/stopped` | GET | Static "app has stopped" page |
| `/heartbeat` | POST | Resets the watchdog timer |

## Flask App Standard Features

- **Quit button** — top-right of header, sends `POST /quit`
- **Heartbeat** — JS `setInterval` every 5 s
- **Watchdog** — daemon thread, exits after 12 s no heartbeat
- **`debug=False`** — PyInstaller requirement
- **`host='0.0.0.0'`** — macOS Sequoia requirement

## Adding news sources

Add an entry to `NEWS_SOURCES` in `app.py`:

```python
{"name": "Source Name", "url": "https://example.com/rss", "default_country": "Country", "filter_ai": True},
```

Set `filter_ai: True` for general tech feeds (applies AI keyword filtering).
Set `filter_ai: False` for dedicated AI feeds (all articles pass through).

## Adding country detection

Add patterns to `_COUNTRY_PATTERNS` in `app.py`:

```python
"New Country": [r"\bNew Country\b", r"\bCapital City\b", r"\bMajor Company\b"],
```

Then add the flag emoji and hex color to `_COUNTRY_FLAGS` / `_COUNTRY_COLORS` in the Python dicts,
and to the `CC` object in the embedded JavaScript.
