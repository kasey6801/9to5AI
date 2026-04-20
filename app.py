"""
9to5AI — AI News Aggregator
============================
Version: v0.42.1

A self-contained Flask web application that aggregates AI news from multiple
public RSS feeds and presents them in a 9to5Mac-inspired interface.

Stories are sorted by date (newest first), tagged by country of coverage,
and filterable by keyword and date range. No API keys required.

===========================================================================
SETUP & INSTALLATION — macOS
===========================================================================

REQUIREMENTS:
    Python 3.10 or higher.

ONE-TIME SETUP:
    cd /path/to/CC_9to5_AI_2
    python3 -m venv .venv
    source .venv/bin/activate
    pip install flask feedparser beautifulsoup4 lxml requests certifi

RUNNING THE APP:
    source .venv/bin/activate
    python app.py

    Opens automatically at http://127.0.0.1:5002
    Stop with the Quit button or Ctrl+C.

BUILDING (.app + .dmg for macOS distribution):
    bash build.sh
    Outputs dist/9to5AI.app and dist/9to5AI.dmg
===========================================================================
"""

from flask import Flask, request, jsonify, render_template_string, Response
import base64
import feedparser
import threading
import webbrowser
import os
import re
import time
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

try:
    from bs4 import BeautifulSoup
    _BS4 = True
except ImportError:
    _BS4 = False

try:
    import requests as _requests
    import certifi as _certifi
    _REQUESTS = True
except ImportError:
    _REQUESTS = False

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Flask(__name__)

# ---------------------------------------------------------------------------
# RSS news sources covering AI globally
# ---------------------------------------------------------------------------

NEWS_SOURCES = [
    # ── Employment Trends (2) ──────────────────────────────────────────────
    {"name": "Indeed Hiring Lab",           "url": "https://hiringlab.org/feed/",                                                  "default_country": "United States", "filter_ai": False, "theme": "Employment Trends"},
    {"name": "Economic Policy Institute",   "url": "https://www.epi.org/blog/feed/",                                               "default_country": "United States", "filter_ai": False, "theme": "Employment Trends"},
    # ── News (10) ──────────────────────────────────────────────────────────
    {"name": "TechCrunch AI",               "url": "https://techcrunch.com/tag/artificial-intelligence/feed/",                     "default_country": "United States", "filter_ai": False, "theme": "News"},
    {"name": "VentureBeat AI",              "url": "https://venturebeat.com/category/ai/feed/",                                    "default_country": "United States", "filter_ai": False, "theme": "News"},
    {"name": "The Verge AI",                "url": "https://www.verge.com/ai-artificial-intelligence.rss",                         "default_country": "United States", "filter_ai": False, "theme": "News"},
    {"name": "MIT Tech Review",             "url": "https://www.technologyreview.com/feed/",                                       "default_country": "United States", "filter_ai": False, "theme": "News"},
    {"name": "Wired AI",                    "url": "https://www.wired.com/feed/tag/ai/latest/",                                    "default_country": "United States", "filter_ai": False, "theme": "News"},
    {"name": "Ars Technica AI",             "url": "https://arstechnica.com/ai/feed/",                                             "default_country": "United States", "filter_ai": False, "theme": "News"},
    {"name": "BBC Technology",              "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",                             "default_country": "United Kingdom","filter_ai": True,  "theme": "News"},
    {"name": "ZDNet AI",                    "url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",                  "default_country": "United States", "filter_ai": True,  "theme": "News"},
    {"name": "Engadget",                    "url": "https://www.engadget.com/rss.xml",                                             "default_country": "United States", "filter_ai": True,  "theme": "News"},
    {"name": "IEEE Spectrum AI",            "url": "https://spectrum.ieee.org/topic/artificial-intelligence/rss",                  "default_country": "United States", "filter_ai": False, "theme": "News"},
    # ── Research (4) ───────────────────────────────────────────────────────
    {"name": "OpenAI News",                 "url": "https://openai.com/news/rss.xml",                                              "default_country": "United States", "filter_ai": False, "theme": "Research"},
    {"name": "Google AI Blog",              "url": "https://ai.googleblog.com/atom.xml",                                           "default_country": "United States", "filter_ai": False, "theme": "Research"},
    {"name": "Hugging Face Blog",           "url": "https://huggingface.co/blog/feed.xml",                                         "default_country": "France",        "filter_ai": False, "theme": "Research"},
    {"name": "DeepMind Blog",               "url": "https://deepmind.google/discover/blog/rss/",                                   "default_country": "United Kingdom","filter_ai": False, "theme": "Research"},
    # ── Transformation (3) ─────────────────────────────────────────────────
    {"name": "McKinsey Insights",           "url": "https://www.mckinsey.com/insights/rss",                                        "default_country": "United States", "filter_ai": True,  "theme": "Transformation"},
    {"name": "Deloitte Insights Podcast",   "url": "https://deloitteuniversitypress.libsyn.com/rss",                               "default_country": "United States", "filter_ai": True,  "theme": "Transformation"},
    {"name": "Change Management Review",    "url": "https://changemanagementreview.com/feed/",                                     "default_country": "United States", "filter_ai": True,  "theme": "Transformation"},
    # ── EU (5) ─────────────────────────────────────────────────────────────
    {"name": "EU AI Act",                   "url": "https://artificialintelligenceact.eu/feed/",                                   "default_country": "Belgium",       "filter_ai": False, "theme": "EU"},
    {"name": "EC Digital Strategy",         "url": "https://digital-strategy.ec.europa.eu/en/policies/rss.xml",                    "default_country": "Belgium",       "filter_ai": True,  "theme": "EU"},
    {"name": "Sifted AI/Europe",            "url": "https://sifted.eu/rss/",                                                       "default_country": "United Kingdom","filter_ai": True,  "theme": "EU"},
    {"name": "Euractiv EU Tech",            "url": "https://www.euractiv.com/section/digital/rss/",                                "default_country": "Belgium",       "filter_ai": True,  "theme": "EU"},
    {"name": "EDPS AI",                     "url": "https://edps.europa.eu/rss.xml",                                               "default_country": "Belgium",       "filter_ai": True,  "theme": "EU"},
    # ── USA (5) ────────────────────────────────────────────────────────────
    {"name": "NIST Information Technology", "url": "https://www.nist.gov/news-events/information%20technology/rss.xml",            "default_country": "United States", "filter_ai": True,  "theme": "USA"},
    {"name": "Nextgov",                     "url": "https://www.nextgov.com/rss/all/",                                             "default_country": "United States", "filter_ai": True,  "theme": "USA"},
    {"name": "Defense One",                 "url": "https://www.defenseone.com/rss/all/",                                          "default_country": "United States", "filter_ai": True,  "theme": "USA"},
    {"name": "GovCIO Media AI",             "url": "https://governmentciomedia.com/tag/artificial-intelligence/feed/",             "default_country": "United States", "filter_ai": False, "theme": "USA"},
    {"name": "FedScoop AI",                 "url": "https://fedscoop.com/category/ai/feed/",                                       "default_country": "United States", "filter_ai": False, "theme": "USA"},
    # ── OCM (2) ────────────────────────────────────────────────────────────
    {"name": "Kotter Inc.",                 "url": "https://www.kotterinc.com/feed/",                                              "default_country": "United States", "filter_ai": True,  "theme": "OCM"},
    {"name": "MIT Sloan Management Review", "url": "https://sloanreview.mit.edu/feed/",                                            "default_country": "United States", "filter_ai": True,  "theme": "OCM"},
    # ── Canada (2) ─────────────────────────────────────────────────────────
    {"name": "CD Howe Institute",           "url": "https://cdhowe.org/feed/",                                                     "default_country": "Canada",        "filter_ai": True,  "theme": "Canada"},
    {"name": "Open North",                  "url": "https://opennorth.ca/feed/",                                                   "default_country": "Canada",        "filter_ai": True,  "theme": "Canada"},
    # ── Africa (3) ─────────────────────────────────────────────────────────
    {"name": "Smart Africa AI",             "url": "https://smartafrica.org/feed/",                                                "default_country": "Rwanda",        "filter_ai": True,  "theme": "Africa"},
    {"name": "CIPESA AI Policy",            "url": "https://cipesa.org/feed/",                                                     "default_country": "South Africa",  "filter_ai": True,  "theme": "Africa"},
    {"name": "Just Security",               "url": "https://www.justsecurity.org/feed/",                                           "default_country": "United States", "filter_ai": True,  "theme": "Africa"},
    # ── Asia (3) ───────────────────────────────────────────────────────────
    {"name": "CSET Georgetown",             "url": "https://cset.georgetown.edu/feed/",                                             "default_country": "United States", "filter_ai": False, "theme": "Asia"},
    {"name": "Japan Digital Agency",        "url": "https://www.digital.go.jp/rss/news.xml",                                       "default_country": "Japan",         "filter_ai": True,  "theme": "Asia"},
    {"name": "Korea AI Times",              "url": "https://www.aitimes.kr/rss/allArticle.xml",                                    "default_country": "South Korea",   "filter_ai": False, "theme": "Asia"},
]

# ---------------------------------------------------------------------------
# Country detection — regex patterns mapped to country names
# ---------------------------------------------------------------------------

_COUNTRY_PATTERNS = {
    "United States": [
        r"\bU\.?S\.?A?\b", r"\bAmerica[n]?\b", r"\bSilicon Valley\b",
        r"\bSan Francisco\b", r"\bNew York\b", r"\bWashington\b", r"\bSeattle\b",
        r"\bOpenAI\b", r"\bAnthropic\b", r"\bGoogle\b", r"\bMicrosoft\b",
        r"\bMeta(?! Quest)\b", r"\bAmazon\b", r"\bNVIDIA\b", r"\bxAI\b",
        r"\bStability AI\b", r"\bPerplexity\b", r"\bRunway\b",
    ],
    "United Kingdom": [
        r"\bU\.?K\.?\b", r"\bBrit(?:ain|ish)\b", r"\bLondon\b", r"\bEngland\b",
        r"\bDeepMind\b", r"\bInflection\b", r"\bArm Holdings\b",
    ],
    "China": [
        r"\bChina\b", r"\bChinese\b", r"\bBeijing\b", r"\bShanghai\b",
        r"\bAlibaba\b", r"\bBaidu\b", r"\bTencent\b", r"\bHuawei\b",
        r"\bByteDance\b", r"\bDeepSeek\b", r"\bQwen\b", r"\bKimi\b",
        r"\bWenxin\b",
    ],
    "France": [
        r"\bFrance\b", r"\bFrench\b", r"\bParis\b", r"\bMistral\b",
        r"\bHugging Face\b",
    ],
    "Germany": [
        r"\bGermany\b", r"\bGerman\b", r"\bBerlin\b", r"\bAleph Alpha\b",
    ],
    "India": [
        r"\bIndia\b", r"\bIndian\b", r"\bBengaluru\b", r"\bMumbai\b",
        r"\bInfosys\b", r"\bTCS\b", r"\bWipro\b",
    ],
    "Canada": [
        r"\bCanada\b", r"\bCanadian\b", r"\bToronto\b", r"\bMontreal\b",
        r"\bCohere\b", r"\bElement AI\b",
    ],
    "Japan": [
        r"\bJapan(?:ese)?\b", r"\bTokyo\b", r"\bSoftBank\b", r"\bSakana AI\b",
    ],
    "South Korea": [
        r"\bSouth Korea\b", r"\bKorean\b", r"\bSeoul\b", r"\bSamsung\b",
        r"\bNaver\b", r"\bKakao\b", r"\bHyperCLOVA\b",
    ],
    "Israel": [
        r"\bIsrael[i]?\b", r"\bTel Aviv\b", r"\bAI21\b",
    ],
    "Australia": [
        r"\bAustralia[n]?\b", r"\bSydney\b", r"\bMelbourne\b",
    ],
    "UAE": [
        r"\bUAE\b", r"\bDubai\b", r"\bAbu Dhabi\b",
        r"\bTechnology Innovation Institute\b", r"\bFalcon\b", r"\bG42\b",
    ],
}

_AI_KEYWORDS = [
    "artificial intelligence", " ai ", "machine learning", "deep learning",
    "neural network", "llm", "large language model", "chatgpt", "claude",
    "gemini", "gpt-", "generative ai", "openai", "anthropic", "deepmind",
    "foundation model", "diffusion model", "ai model", "ai system",
    "ai chip", "ai safety", "ai regulation", "transformer model",
]


def _detect_countries(text: str) -> list:
    found = []
    for country, patterns in _COUNTRY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                found.append(country)
                break
    return found


def _is_ai_related(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _AI_KEYWORDS)


def _extract_image(entry) -> str | None:
    # media_content / media_thumbnail
    for attr in ("media_content", "media_thumbnail"):
        items = getattr(entry, attr, None) or []
        for item in items:
            url = item.get("url", "")
            if url and not url.split("?")[0].endswith((".mp4", ".webm")):
                return url

    # enclosures
    for enc in getattr(entry, "enclosures", []):
        if enc.get("type", "").startswith("image/"):
            return enc.get("href") or enc.get("url")

    # Parse from HTML body
    html = ""
    if hasattr(entry, "content") and entry.content:
        html = entry.content[0].get("value", "")
    if not html:
        html = entry.get("summary", "")

    if html and _BS4:
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img")
        if img:
            src = img.get("src", "")
            if src.startswith("http"):
                return src

    return None


def _parse_date(entry) -> datetime:
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        val = getattr(entry, field, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return datetime.now(timezone.utc)


def _clean_html(html: str) -> str:
    if not html:
        return ""
    if _BS4:
        return BeautifulSoup(html, "html.parser").get_text(separator=" ").strip()
    return re.sub(r"<[^>]+>", " ", html).strip()


def _fetch_feed(source: dict) -> list:
    articles = []
    try:
        headers = {"User-Agent": "9to5AI/1.0 (+https://github.com/9to5ai)"}
        if _REQUESTS:
            resp = _requests.get(source["url"], headers=headers, timeout=15,
                                 verify=_certifi.where())
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        else:
            feed = feedparser.parse(source["url"], request_headers=headers)
        for entry in feed.entries[:25]:
            title = (entry.get("title") or "").strip()
            if not title:
                continue

            link = entry.get("link", "")

            html_body = ""
            if hasattr(entry, "content") and entry.content:
                html_body = entry.content[0].get("value", "")
            if not html_body:
                html_body = entry.get("summary", "")

            summary = _clean_html(html_body)
            summary = re.sub(r"\s+", " ", summary)[:400]

            combined = f"{title} {summary}"

            if source.get("filter_ai") and not _is_ai_related(combined):
                continue

            pub_date = _parse_date(entry)
            image_url = _extract_image(entry)
            countries = _detect_countries(combined) or [source.get("default_country", "")]

            articles.append({
                "title":    title,
                "link":     link,
                "summary":  summary,
                "source":   source["name"],
                "date":     pub_date.isoformat(),
                "date_ts":  pub_date.timestamp(),
                "image":    image_url,
                "countries": countries,
                "themes":   [source["theme"]] if source.get("theme") else [],
            })
    except Exception as exc:
        print(f"[9to5AI] Feed error ({source['name']}): {exc}")
    return articles


# ---------------------------------------------------------------------------
# Article cache — refreshed every 5 minutes
# ---------------------------------------------------------------------------

_cache: list = []
_cache_ts: float = 0.0
_cache_lock = threading.Lock()
_CACHE_TTL = 300


def _get_articles() -> list:
    global _cache, _cache_ts
    now = time.monotonic()
    with _cache_lock:
        if now - _cache_ts > _CACHE_TTL or not _cache:
            with ThreadPoolExecutor(max_workers=20) as pool:
                results = list(pool.map(_fetch_feed, NEWS_SOURCES))
            flat = [a for r in results for a in r]
            seen: set = set()
            deduped = []
            for a in flat:
                key = a["link"] or a["title"]
                if key not in seen:
                    seen.add(key)
                    deduped.append(a)
            _cache = deduped
            _cache_ts = now
        return list(_cache)


# ---------------------------------------------------------------------------
# Favicon — SVG served from /favicon.svg (most reliable in Chromium/Brave)
# ---------------------------------------------------------------------------

_FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='6' fill='#131313'/>"
    "<text x='16' y='23' font-family='Arial Black,sans-serif' font-size='20' "
    "font-weight='900' fill='#e8363d' text-anchor='middle'>9</text>"
    "</svg>"
)

# ---------------------------------------------------------------------------
# Favicon — ICO + PNG fallbacks
# ---------------------------------------------------------------------------

_FAVICON_ICO = (
    "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"
)

_FAVICON_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAFCElEQVR4nO2bTWwbRRTH/zveXa+/"
    "k7hp66RJCWn5FIgWJC4gJIjg0AoqEKISJ0AIwQXECaRK5cCpRUIgUA4U6AGpBw4IlUaq+BIqlK/C"
    "haJWQEFp3DiJs44d22vHX4tmhKvdjT/Wrtfy7vKTHMuzO8/7nmfevPdmwqEF0WhUhQOQZZlrdo1z"
    "suJmDEHconwz3Ui7G5yGUUfS7IKT0epKjA1uoa4zgcvh3PjrayFwOQQuh8Dl8P34Ehp+7ZH8eCAQ"
    "wl0+P7Z4eIx4eFRUFalqFRdLRXyv5DCXW8d6rdqPR+qfE7xBlHB4NIY7JF/bewu1Gt5Lr+JYWkZV"
    "Ve1vgIeCYRzdOg4P1zQXaciPhTxeXFpAtlaDbX3APf4gjnShPOVuXwBvbZ8A30XfgRgBYeLBqclp"
    "Ns+1xMslHM+k8J2Sw0qlDIEjuF4U8WAgjIOREUgGhWfXkngnlYTtDPDaaAyPh4d1bXO5DA6tLGKj"
    "ydyeEETMxiYxJYhX28qqiv0Ll5jhbDMFRjw8DoSGdG0/FfJ4ZflKU+UpC+USnl2c160CAsfhqaEo"
    "rIT0WuCjoSH24HWoOoeTCfbejkSljFnDkH8kGIHEWReukF4LvC8Q1H0+k8/icgdD+JNsWrcE+ghh"
    "DtUWBhA4Drd69ev9GSXXkQy69P1R2tC13WsXA4zzArwGT36hVOxYzj+GEXO7JMEWBoh4PJva1qqd"
    "h7ZZQzg8LUoQLYoJSC+F+Ro4q1aevxlGKdSsW3nhGp7M/HddE41C1yAhXQVSRmI8P/gGSFcrDQOc"
    "TmnUJ0JsYIBEpbxp/u4xkQVq8ROCG0XvpnZjmDyQBqgB+LVY0LXtC0bYHO4kkGqUQEnEBgagnM5l"
    "oCXGC3gyMgIzjPECnhve0vBa1aKknfRaIK3qJA2+4OXoNlYNalc4OTa2c1MGWaeoWlMb4HstkGZw"
    "R1eXcWTbuC5CfHv7BL7Ir+PTbAbnNwosPqAx/k1eCfuDERwIRa7m/+p/crRrf9GiChFvhdBTuQyL"
    "3x8ORXTtM4Ewe7XjRCbFMkqtAdJdBFRmIJZIBXAouYiTWb0/MMO3So7VBelqoGWpUoatDFBVVby6"
    "cgWvryZMhcO0Qvx+WsYLSwvYwevjANp7pUGMMfBlcZUN5zV8ls2woU9T5d2ihKiHZ8M7WakgXinh"
    "63wWpzXOc5chDqDptFVVYh59gIbINM+nLzPc4tVnf79v6GMLx+8M7ZX8us/nDcGVow0w6uExbZgC"
    "Zwt59xhgJhjaNP8vGSpEA+0D5iZ3Yacmm3tDXsaHadl0/8dC+nL65/ksrIT0WqBsWK6MNcJW3B8I"
    "4WaNA6R+/+P1NdjKAL8ZHNZMIMQSIjP1RLqJquWbfJbtF9jKAF8p+iFbzwOaJTmU3aIXH4xdx7bN"
    "tcHPm6kVWA3fa4HnCgp+KSq4U7OU0XX95MQ0Psqk8GV+HfFKmVl+SvBiXyiCg+Fh3WYK5Xhaxl8W"
    "Oj9L9wanRS9OjE8h0EU9sG7EpxPzfTkjQKwQSpetl5bjyHexv/9zQcHzS5f7dkCCWCX4rJLDE/G/"
    "mUJmoOXzd1NJPJOYh9KHgxF9PSd4m9fHKkJ7fX7s4AW2gULAIVOr4s/SBn5QcixPoOeF+g33/0FJ"
    "l0PgcghcDoHLIXA5BC6HwOUQuBzS6p8KnY4syxYewLMJhP5x4yio60yMDW5AqytpdsGpGHUk7W5w"
    "Eo1041p1cEqq3OpH/ReliNTXmY7CbwAAAABJRU5ErkJggg=="
)

# ---------------------------------------------------------------------------
# Embedded frontend — 9to5Mac-inspired design for AI news
# ---------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>9 to 5 AI</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" type="image/png" href="/favicon.png">
  <link rel="shortcut icon" type="image/x-icon" href="/favicon.ico">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    /* ── Tokens — dark mode default ── */
    :root {
      --hdr:    #131313;
      --bg:     #141414;
      --card:   #1e1e1e;
      --text:   #f0f0f0;
      --sub:    #b0b0b0;
      --muted:  #707070;
      --border: rgba(255,255,255,0.12);
      --card-border: rgba(255,255,255,0.08);
      --card-shadow: 0 1px 4px rgba(0,0,0,0.4), 0 6px 20px rgba(0,0,0,0.3);
      --pill-bg:      transparent;
      --pill-border:  rgba(255,255,255,0.22);
      --pill-text:    rgba(255,255,255,0.65);
      --pill-act-bg:  rgba(255,255,255,0.1);
      --pill-act-bdr: rgba(255,255,255,0.38);
      --pill-act-txt: #ffffff;
      --cnt-bg:       rgba(255,255,255,0.12);
      --cnt-txt:      rgba(255,255,255,0.55);
      --cnt-act-bg:   rgba(255,255,255,0.18);
      --cnt-act-txt:  #ffffff;
      --red:    #e8363d;
      --radius: 12px;
    }

    /* ── Light mode — toggled by .light on <html> ── */
    html.light {
      --bg:     #f2f2f7;
      --card:   #ffffff;
      --text:   #1d1d1f;
      --sub:    #3a3a3c;
      --muted:  #6e6e73;
      --border: rgba(0,0,0,0.08);
      --card-border: rgba(0,0,0,0.06);
      --card-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 6px 20px rgba(0,0,0,0.06);
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      transition: background 0.2s, color 0.2s;
    }

    /* ═══════════════════════════════════════════════
       SITE HEADER — always dark regardless of theme
    ═══════════════════════════════════════════════ */
    .site-header {
      background: var(--hdr);
      position: sticky;
      top: 0;
      z-index: 200;
      box-shadow: 0 1px 0 rgba(255,255,255,0.05), 0 4px 24px rgba(0,0,0,0.6);
    }

    /* ── Top row: brand left, meta+controls right ── */
    .header-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 32px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    /* Brand */
    .brand {}
    .brand-title {
      font-size: 1.75rem;
      font-weight: 900;
      cursor: pointer;
      letter-spacing: -0.5px;
      color: #ffffff;
      line-height: 1;
    }
    .brand-sub {
      font-size: 0.62rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1.4px;
      color: rgba(255,255,255,0.35);
      margin-top: 5px;
    }

    /* Right controls */
    .header-right {
      display: flex;
      align-items: center;
      gap: 18px;
    }
    .header-meta {
      text-align: right;
      line-height: 1.35;
    }
    .header-date {
      font-size: 0.82rem;
      color: rgba(255,255,255,0.7);
    }
    .header-time {
      font-size: 0.78rem;
      color: rgba(255,255,255,0.55);
      font-variant-numeric: tabular-nums;
      margin-top: 1px;
    }
    .header-count {
      font-size: 0.78rem;
      color: rgba(255,255,255,0.38);
      margin-top: 1px;
    }

    /* Light/dark toggle */
    #theme-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      background: transparent;
      border: 1px solid rgba(255,255,255,0.25);
      border-radius: 999px;
      color: rgba(255,255,255,0.75);
      padding: 6px 16px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: border-color 0.15s, color 0.15s;
      white-space: nowrap;
    }
    #theme-btn:hover { border-color: rgba(255,255,255,0.5); color: #fff; }

    /* Quit */
    #quit-btn {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.16);
      color: rgba(255,255,255,0.38);
      border-radius: 6px;
      padding: 6px 13px;
      font-size: 0.78rem;
      cursor: pointer;
      transition: border-color 0.15s, color 0.15s;
    }
    #quit-btn:hover { border-color: var(--red); color: var(--red); }

    /* Shutdown overlay */
    #shutdown-overlay {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 9999;
      background: rgba(0,0,0,0.72);
      backdrop-filter: blur(6px);
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: 16px;
    }
    #shutdown-overlay.visible { display: flex; }
    .shutdown-spinner {
      width: 36px; height: 36px;
      border: 3px solid rgba(255,255,255,0.15);
      border-top-color: var(--red);
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .shutdown-msg {
      color: rgba(255,255,255,0.85);
      font-size: 1rem;
      font-weight: 500;
      letter-spacing: 0.02em;
    }

    /* ── Filter bar ── */
    .filter-bar {
      display: flex;
      align-items: center;
      gap: 18px;
      padding: 13px 32px 16px;
      flex-wrap: wrap;
    }
    .filter-label {
      font-size: 0.62rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.2px;
      color: rgba(255,255,255,0.32);
      white-space: nowrap;
    }
    .filter-pills {
      display: flex;
      gap: 9px;
      flex-wrap: wrap;
      align-items: center;
    }

    /* Date-range pills */
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      background: var(--pill-bg);
      border: 1px solid var(--pill-border);
      border-radius: 999px;
      padding: 7px 15px;
      color: var(--pill-text);
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s, color 0.15s;
      white-space: nowrap;
    }
    .pill:hover {
      border-color: rgba(255,255,255,0.38);
      color: rgba(255,255,255,0.85);
    }
    .pill.active {
      background: var(--pill-act-bg);
      border-color: var(--pill-act-bdr);
      color: var(--pill-act-txt);
    }
    .pill-check { font-size: 0.72rem; display: none; }
    .pill.active .pill-check { display: inline; }
    .pill-name {}
    .pill-cnt {
      background: var(--cnt-bg);
      color: var(--cnt-txt);
      border-radius: 999px;
      padding: 1px 8px;
      font-size: 0.7rem;
      font-weight: 700;
      min-width: 22px;
      text-align: center;
      transition: background 0.15s, color 0.15s;
    }
    .pill.active .pill-cnt {
      background: var(--cnt-act-bg);
      color: var(--cnt-act-txt);
    }

    /* Search row (below header, above grid) */
    .search-row {
      display: flex;
      align-items: center;
      gap: 10px;
      max-width: 1280px;
      margin: 22px auto 0;
      padding: 0 24px;
    }
    .search-wrap {
      position: relative;
      flex: 1;
      max-width: 480px;
    }
    .search-icon {
      position: absolute;
      left: 11px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--muted);
      font-size: 13px;
      pointer-events: none;
    }
    #q {
      width: 100%;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px 8px 30px;
      color: var(--text);
      font-size: 0.88rem;
      outline: none;
      transition: border-color 0.15s;
    }
    #q:focus { border-color: var(--red); }
    #q::placeholder { color: var(--muted); }
    #go {
      background: var(--red);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 8px 20px;
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.15s;
    }
    #go:hover { background: #c8252b; }
    #go:disabled { background: #555; cursor: default; }

    /* ═══════════════════════════════════════════════
       MAIN CONTENT
    ═══════════════════════════════════════════════ */
    .page {
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 24px 80px;
    }

    /* ── States ── */
    .center-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 90px 20px;
      color: var(--muted);
      text-align: center;
    }
    .spinner {
      width: 38px;
      height: 38px;
      border: 3px solid rgba(232,54,61,0.2);
      border-top-color: var(--red);
      border-radius: 50%;
      animation: spin 0.65s linear infinite;
      margin-bottom: 18px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .center-state p { font-size: 0.9rem; }
    .err-icon { font-size: 2rem; margin-bottom: 10px; }

    /* ── Grid ── */
    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
    }
    @media (max-width: 1020px) { .grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 640px)  { .grid { grid-template-columns: 1fr; } }

    /* ── Card ── */
    .card {
      background: var(--card);
      border-radius: var(--radius);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: var(--card-shadow);
      border: 1px solid var(--card-border);
      cursor: pointer;
      transition: transform 0.18s, box-shadow 0.18s;
      text-decoration: none;
      color: inherit;
    }
    .card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.25), 0 20px 48px rgba(0,0,0,0.18);
    }

    .card-img-wrap {
      width: 100%;
      height: 192px;
      overflow: hidden;
      flex-shrink: 0;
      background: linear-gradient(135deg, #0f0f1e 0%, #181830 55%, #0c1628 100%);
      position: relative;
    }
    .card-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.3s;
    }
    .card:hover .card-img { transform: scale(1.04); }
    .card-placeholder {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0.15;
    }

    .card-body {
      padding: 14px 15px 15px;
      display: flex;
      flex-direction: column;
      flex: 1;
    }
    .card-meta {
      display: flex;
      align-items: center;
      gap: 7px;
      margin-bottom: 7px;
    }
    .card-source {
      font-size: 0.67rem;
      font-weight: 700;
      color: var(--red);
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }
    .dot { width: 3px; height: 3px; border-radius: 50%; background: var(--muted); opacity: 0.5; }
    .card-date { font-size: 0.67rem; color: var(--muted); }

    .card-title {
      font-size: 0.95rem;
      font-weight: 700;
      line-height: 1.42;
      color: var(--text);
      margin-bottom: 7px;
      flex: 1;
      transition: color 0.12s;
    }
    .card:hover .card-title { color: var(--red); }

    .card-excerpt {
      font-size: 0.79rem;
      color: var(--sub);
      line-height: 1.55;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin-bottom: 12px;
    }

    .card-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-top: auto;
    }
    .ctag {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 3px 9px;
      border-radius: 999px;
      font-size: 0.65rem;
      font-weight: 700;
      color: #fff;
    }
    .ttag {
      display: inline-flex;
      align-items: center;
      padding: 3px 9px;
      border-radius: 999px;
      font-size: 0.65rem;
      font-weight: 600;
      color: rgba(255,255,255,0.75);
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.12);
    }
    .light .ttag {
      color: rgba(0,0,0,0.55);
      background: rgba(0,0,0,0.06);
      border-color: rgba(0,0,0,0.1);
    }
    .card-utc {
      font-size: 0.65rem;
      color: var(--muted);
      margin-top: 6px;
      font-variant-numeric: tabular-nums;
    }
    .cdr-in {
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.22);
      border-radius: 8px;
      padding: 6px 9px;
      color: #fff;
      font-size: 0.78rem;
      outline: none;
      cursor: pointer;
      transition: border-color 0.15s;
    }
    .cdr-in:focus { border-color: rgba(255,255,255,0.5); }
    .cdr-in::-webkit-calendar-picker-indicator { filter: invert(0.6); cursor: pointer; }
    .cdr-sep { color: rgba(255,255,255,0.35); font-size: 0.8rem; }
    .no-results { grid-column: 1/-1; }

    /* ── Theme filter row ── */
    .theme-bar {
      display: flex;
      align-items: center;
      gap: 18px;
      padding: 0 32px 14px;
      flex-wrap: wrap;
    }
    .theme-wrap { position: relative; }
    .theme-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--pill-bg);
      border: 1px solid var(--pill-border);
      border-radius: 8px;
      padding: 7px 14px;
      color: var(--pill-text);
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      transition: border-color 0.15s, color 0.15s;
      white-space: nowrap;
    }
    .theme-btn:hover, .theme-btn.open {
      border-color: rgba(255,255,255,0.38);
      color: rgba(255,255,255,0.85);
    }
    .theme-btn.has-selection {
      border-color: var(--pill-act-bdr);
      color: var(--pill-act-txt);
      background: var(--pill-act-bg);
    }
    .theme-caret { font-size: 0.65rem; opacity: 0.6; }
    .theme-dropdown {
      display: none;
      position: absolute;
      top: calc(100% + 6px);
      left: 0;
      z-index: 300;
      background: #242424;
      border: 1px solid rgba(255,255,255,0.14);
      border-radius: 10px;
      padding: 8px 0;
      min-width: 220px;
      max-height: 340px;
      overflow-y: auto;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .theme-dropdown.open { display: block; }
    .theme-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 16px;
      cursor: pointer;
      font-size: 0.82rem;
      color: rgba(255,255,255,0.7);
      transition: background 0.1s, color 0.1s;
      user-select: none;
    }
    .theme-item:hover { background: rgba(255,255,255,0.06); color: #fff; }
    .theme-item.checked { color: #fff; }
    .theme-checkbox {
      width: 15px; height: 15px;
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 4px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
      font-size: 0.65rem;
      transition: background 0.12s, border-color 0.12s;
    }
    .theme-item.checked .theme-checkbox {
      background: var(--red);
      border-color: var(--red);
    }
    .theme-divider { height: 1px; background: rgba(255,255,255,0.08); margin: 4px 0; }
    .theme-clear {
      display: flex;
      align-items: center;
      padding: 7px 16px;
      font-size: 0.75rem;
      color: rgba(255,255,255,0.38);
      cursor: pointer;
      transition: color 0.12s;
    }
    .theme-clear:hover { color: var(--red); }
    .theme-chips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    .theme-chip {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: rgba(232,54,61,0.15);
      border: 1px solid rgba(232,54,61,0.35);
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 0.75rem;
      color: rgba(255,255,255,0.85);
      cursor: pointer;
    }
    .theme-chip:hover { background: rgba(232,54,61,0.25); }
    .theme-chip-x { font-size: 0.7rem; opacity: 0.6; }
  </style>
</head>
<body>
<div id="shutdown-overlay">
  <div class="shutdown-spinner"></div>
  <div class="shutdown-msg">Shutting down…</div>
</div>

<!-- ═══ SITE HEADER ═══ -->
<header class="site-header">

  <!-- Top row -->
  <div class="header-top">
    <div class="brand">
      <div class="brand-title" onclick="resetFilters()" title="Clear all filters">9 to 5 AI</div>
      <div class="brand-sub">39 sources &middot; Employment Trends | News | Research | Transformation | EU | USA | OCM | Canada | Africa | Asia</div>
    </div>
    <div class="header-right">
      <div class="header-meta">
        <div class="header-date" id="hdr-date"></div>
        <div class="header-time" id="hdr-time"></div>
        <div class="header-count" id="hdr-count">&nbsp;</div>
      </div>
      <button id="theme-btn" onclick="toggleTheme()">&#9728; Light</button>
      <button id="quit-btn" onclick="quitApp()">Quit</button>
    </div>
  </div>

  <!-- Filter bar -->
  <div class="filter-bar">
    <span class="filter-label">Filter by Date</span>
    <div class="filter-pills">
      <button class="pill" data-days="1" onclick="selectPill(this,1)">
        <span class="pill-check">&#10003;</span>
        <span class="pill-name">Today</span>
        <span class="pill-cnt" id="cnt-1">&ndash;</span>
      </button>
      <button class="pill active" data-days="30" onclick="selectPill(this,30)">
        <span class="pill-check">&#10003;</span>
        <span class="pill-name">30 days</span>
        <span class="pill-cnt" id="cnt-30">&ndash;</span>
      </button>
      <button class="pill" data-days="60" onclick="selectPill(this,60)">
        <span class="pill-check">&#10003;</span>
        <span class="pill-name">60 days</span>
        <span class="pill-cnt" id="cnt-60">&ndash;</span>
      </button>
      <button class="pill" data-days="90" onclick="selectPill(this,90)">
        <span class="pill-check">&#10003;</span>
        <span class="pill-name">90 days</span>
        <span class="pill-cnt" id="cnt-90">&ndash;</span>
      </button>
      <button class="pill" id="pill-custom" onclick="selectCustom(this)">
        <span class="pill-check">&#10003;</span>
        <span class="pill-name">Custom</span>
      </button>
      <div id="custom-range" style="display:none;align-items:center;gap:7px;">
        <input type="date" id="cdr-from" class="cdr-in" onchange="applyCustomRange()" />
        <span class="cdr-sep">&ndash;</span>
        <input type="date" id="cdr-to"   class="cdr-in" onchange="applyCustomRange()" />
      </div>
    </div>
  </div>

  <!-- Theme filter row -->
  <div class="theme-bar">
    <span class="filter-label">Filter by Theme</span>
    <div class="theme-wrap">
      <button class="theme-btn" id="theme-toggle-btn" onclick="toggleThemeDropdown()">
        <span id="theme-btn-label">All Themes</span>
        <span class="theme-caret">&#9660;</span>
      </button>
      <div class="theme-dropdown" id="theme-dropdown">
        <div class="theme-clear" onclick="clearThemes()">Clear all</div>
        <div class="theme-divider"></div>
      </div>
    </div>
    <div class="theme-chips" id="theme-chips"></div>
  </div>
</header>

<!-- ═══ SEARCH ROW ═══ -->
<div class="search-row">
  <div class="search-wrap">
    <span class="search-icon">&#128269;</span>
    <input type="text" id="q" placeholder="Search AI news&hellip;" />
  </div>
  <button id="go" onclick="applyFilters()">Search</button>
</div>

<!-- ═══ MAIN CONTENT ═══ -->
<div class="page">
  <div id="view">
    <div class="center-state">
      <div class="spinner"></div>
      <p>Fetching AI news&hellip;</p>
    </div>
  </div>
</div>

<script>
// ── Country metadata ──────────────────────────────────────────────────────────
const CC = {
  "United States": { flag: "🇺🇸", color: "#1d4ed8" },
  "United Kingdom": { flag: "🇬🇧", color: "#dc2626" },
  "China":          { flag: "🇨🇳", color: "#b45309" },
  "France":         { flag: "🇫🇷", color: "#7c3aed" },
  "Germany":        { flag: "🇩🇪", color: "#374151" },
  "India":          { flag: "🇮🇳", color: "#ea580c" },
  "Canada":         { flag: "🇨🇦", color: "#b91c1c" },
  "Japan":          { flag: "🇯🇵", color: "#be185d" },
  "South Korea":    { flag: "🇰🇷", color: "#0e7490" },
  "Israel":         { flag: "🇮🇱", color: "#0369a1" },
  "Australia":      { flag: "🇦🇺", color: "#15803d" },
  "UAE":            { flag: "🇦🇪", color: "#6d28d9" },
};

const THEMES = [
  "Employment Trends","News","Research","Transformation",
  "EU","USA","OCM","Canada","Africa","Asia",
];

// ── State ──────────────────────────────────────────────────────────────────────
let allArticles   = [];
let activeDays    = 30;
let customRange   = null; // {from: Date, to: Date} when custom mode active
let isLight       = false;
let activeThemes  = new Set();

// ── Helpers ───────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
                      .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}
function utcTime(iso) {
  if (!iso) return "";
  const d = new Date(iso); if (isNaN(d)) return "";
  const hh = String(d.getUTCHours()).padStart(2,"0");
  const mm = String(d.getUTCMinutes()).padStart(2,"0");
  const mon = d.toLocaleDateString("en-US",{month:"short",timeZone:"UTC"});
  const day = d.getUTCDate();
  return `${mon} ${day}, ${hh}:${mm} UTC`;
}
function relDate(iso) {
  if (!iso) return "";
  const d = new Date(iso); if (isNaN(d)) return "";
  const diff = Date.now() - d, h = diff / 3600000;
  if (h < 1)  return Math.max(1, Math.round(diff/60000)) + "m ago";
  if (h < 24) return Math.round(h) + "h ago";
  if (h < 48) return "Yesterday";
  return d.toLocaleDateString("en-US", { month:"short", day:"numeric" });
}

// ── Placeholder SVG ───────────────────────────────────────────────────────────
const SVG_PH = `<svg width="72" height="72" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="40" cy="40" r="36" stroke="white" stroke-width="2.5"/>
  <path d="M28 40c0-6.627 5.373-12 12-12s12 5.373 12 12-5.373 12-12 12-12-5.373-12-12z" stroke="white" stroke-width="2"/>
  <path d="M40 28v-8M40 60v-8M28 40h-8M60 40h-8" stroke="white" stroke-width="2" stroke-linecap="round"/>
  <circle cx="40" cy="40" r="4" fill="white"/>
  <path d="M33.17 33.17L27.1 27.1M46.83 46.83l6.07 6.07M46.83 33.17l6.07-6.07M33.17 46.83l-6.07 6.07" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
</svg>`;

// ── Card renderer ─────────────────────────────────────────────────────────────
function renderCard(a) {
  const img  = a.image ? `<img class="card-img" src="${esc(a.image)}" alt="" loading="lazy" onerror="this.style.display='none'">` : "";
  const tags = (a.countries||[]).map(c => {
    const m = CC[c]||{flag:"🌍",color:"#6b7280"};
    return `<span class="ctag" style="background:${m.color}">${m.flag} ${esc(c)}</span>`;
  }).join("");
  const theme = (a.themes||[])[0];
  const ttag  = theme ? `<span class="ttag">${esc(theme)}</span>` : "";
  return `<a class="card" href="${esc(a.link||"#")}" target="_blank" rel="noopener noreferrer">
  <div class="card-img-wrap">${img}<div class="card-placeholder">${SVG_PH}</div></div>
  <div class="card-body">
    <div class="card-meta">
      <span class="card-source">${esc(a.source)}</span>
      <span class="dot"></span>
      <span class="card-date">${relDate(a.date)}</span>
    </div>
    <div class="card-title">${esc(a.title)}</div>
    <div class="card-excerpt">${esc(a.summary)}</div>
    <div class="card-tags">${tags}${ttag}</div>
    <div class="card-utc">${utcTime(a.date)}</div>
  </div>
</a>`;
}

// ── Update pill counts from allArticles ───────────────────────────────────────
function updateCounts() {
  [1,30,60,90].forEach(d => {
    const cutoff = Date.now() - d * 86400000;
    const n = allArticles.filter(a => new Date(a.date).getTime() >= cutoff).length;
    const el = document.getElementById("cnt-" + d);
    if (el) el.textContent = n;
  });
}

// ── Theme dropdown ────────────────────────────────────────────────────────────
function buildThemeDropdown() {
  const dd = document.getElementById("theme-dropdown");
  THEMES.forEach(name => {
    const item = document.createElement("div");
    item.className = "theme-item";
    item.dataset.theme = name;
    item.innerHTML = `<span class="theme-checkbox"></span><span>${esc(name)}</span>`;
    item.onclick = () => toggleThemePick(name);
    dd.appendChild(item);
  });
}
function toggleThemeDropdown() {
  const dd  = document.getElementById("theme-dropdown");
  const btn = document.getElementById("theme-toggle-btn");
  const open = dd.classList.toggle("open");
  btn.classList.toggle("open", open);
  if (open) setTimeout(() => document.addEventListener("click", closeThemeDropdown, {once:true,capture:true}), 0);
}
function closeThemeDropdown(e) {
  const wrap = document.querySelector(".theme-wrap");
  if (wrap && wrap.contains(e.target)) {
    setTimeout(() => document.addEventListener("click", closeThemeDropdown, {once:true,capture:true}), 0);
    return;
  }
  document.getElementById("theme-dropdown").classList.remove("open");
  document.getElementById("theme-toggle-btn").classList.remove("open");
}
function toggleThemePick(name) {
  if (activeThemes.has(name)) activeThemes.delete(name); else activeThemes.add(name);
  syncThemeUI(); applyFilters();
}
function clearThemes() { activeThemes.clear(); syncThemeUI(); applyFilters(); }
function resetFilters() {
  // Clear search
  document.getElementById("q").value = "";
  // Clear theme selection
  activeThemes.clear(); syncThemeUI();
  // Clear custom date range, restore 30-day default pill
  customRange = null;
  document.getElementById("custom-range").style.display = "none";
  document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
  const defaultPill = document.querySelector(".pill[data-days='30']");
  if (defaultPill) { defaultPill.classList.add("active"); activeDays = 30; }
  applyFilters();
}
function syncThemeUI() {
  document.querySelectorAll(".theme-item").forEach(el => {
    const on = activeThemes.has(el.dataset.theme);
    el.classList.toggle("checked", on);
    el.querySelector(".theme-checkbox").textContent = on ? "\u2713" : "";
  });
  const btn = document.getElementById("theme-toggle-btn");
  const lbl = document.getElementById("theme-btn-label");
  if (activeThemes.size === 0) {
    lbl.textContent = "All Themes";
    btn.classList.remove("has-selection");
  } else {
    lbl.textContent = activeThemes.size === 1 ? [...activeThemes][0] : activeThemes.size + " themes";
    btn.classList.add("has-selection");
  }
  document.getElementById("theme-chips").innerHTML = [...activeThemes].map(name =>
    `<span class="theme-chip" onclick="toggleThemePick('${esc(name)}')">${esc(name)}<span class="theme-chip-x">\u2715</span></span>`
  ).join("");
}

// ── Apply date + keyword filter, render grid ──────────────────────────────────
function applyFilters() {
  const q = (document.getElementById("q").value||"").trim().toLowerCase();
  let shown;
  if (customRange) {
    shown = allArticles.filter(a => {
      const t = new Date(a.date).getTime();
      return t >= customRange.from && t <= customRange.to;
    });
  } else {
    const cutoff = Date.now() - activeDays * 86400000;
    shown = allArticles.filter(a => new Date(a.date).getTime() >= cutoff);
  }
  if (q) shown = shown.filter(a => a.title.toLowerCase().includes(q) || a.summary.toLowerCase().includes(q));
  if (activeThemes.size > 0) {
    shown = shown.filter(a => (a.themes||[]).some(t => activeThemes.has(t)));
  }

  document.getElementById("hdr-count").textContent =
    shown.length + " of " + allArticles.length + " stories";

  const view = document.getElementById("view");
  if (!shown.length) {
    view.innerHTML = `<div class="grid"><div class="no-results center-state">
      <div class="err-icon">&#128269;</div>
      <p><strong>No stories found.</strong></p>
      <p style="margin-top:6px;font-size:.83rem">Try a wider date range or different keywords.</p>
    </div></div>`;
  } else {
    view.innerHTML = `<div class="grid">${shown.map(renderCard).join("")}</div>`;
  }
}

// ── Pill selection ────────────────────────────────────────────────────────────
function selectPill(btn, days) {
  document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
  btn.classList.add("active");
  activeDays  = days;
  customRange = null;
  document.getElementById("custom-range").style.display = "none";
  applyFilters();
}

function selectCustom(btn) {
  document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
  btn.classList.add("active");
  customRange = null;
  const wrap = document.getElementById("custom-range");
  wrap.style.display = "flex";
  // Default to last 7 days if inputs are empty
  const today = new Date();
  const from  = document.getElementById("cdr-from");
  const to    = document.getElementById("cdr-to");
  if (!to.value)   to.value   = today.toISOString().slice(0,10);
  if (!from.value) { const d = new Date(today); d.setDate(d.getDate()-7); from.value = d.toISOString().slice(0,10); }
  applyCustomRange();
}

function applyCustomRange() {
  const from = document.getElementById("cdr-from").value;
  const to   = document.getElementById("cdr-to").value;
  if (!from || !to) return;
  customRange = {
    from: new Date(from + "T00:00:00Z").getTime(),
    to:   new Date(to   + "T23:59:59Z").getTime(),
  };
  applyFilters();
}

// ── Theme toggle ──────────────────────────────────────────────────────────────
function toggleTheme() {
  isLight = !isLight;
  document.documentElement.classList.toggle("light", isLight);
  document.getElementById("theme-btn").textContent = isLight ? "\u263D Dark" : "\u2600 Light";
}

// ── Quit ──────────────────────────────────────────────────────────────────────
async function quitApp() {
  document.getElementById("shutdown-overlay").classList.add("visible");
  await fetch("/quit", { method: "POST" });
  setTimeout(() => { window.location.href = "/stopped"; }, 650);
}

// ── Heartbeat ─────────────────────────────────────────────────────────────────
setInterval(() => fetch("/heartbeat",{method:"POST"}).catch(()=>{}), 5000);

// ── Search key binding ────────────────────────────────────────────────────────
document.getElementById("q").addEventListener("keydown", e => {
  if (e.key === "Enter") applyFilters();
});
document.getElementById("q").addEventListener("input", e => {
  if (e.target.value === "") applyFilters();
});

// ── Init ──────────────────────────────────────────────────────────────────────
(async function init() {
  // Set header date and start live UTC clock
  document.getElementById("hdr-date").textContent =
    new Date().toLocaleDateString("en-US", {weekday:"long", month:"long", day:"numeric", year:"numeric"});
  function tickUTC() {
    const n = new Date();
    const hh = String(n.getUTCHours()).padStart(2,"0");
    const mm = String(n.getUTCMinutes()).padStart(2,"0");
    const ss = String(n.getUTCSeconds()).padStart(2,"0");
    document.getElementById("hdr-time").textContent = `${hh}:${mm}:${ss} UTC`;
  }
  tickUTC();
  setInterval(tickUTC, 1000);

  buildThemeDropdown();
  document.getElementById("hdr-count").textContent = "Loading\u2026";

  try {
    const res = await fetch("/fetch", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: "{}",
    });
    if (!res.ok) throw new Error("Server error " + res.status);
    allArticles = await res.json();
    updateCounts();
    applyFilters();
  } catch(e) {
    document.getElementById("view").innerHTML =
      `<div class="center-state"><div class="err-icon">&#10060;</div>
      <p><strong>Could not load news.</strong></p>
      <p style="margin-top:6px;font-size:.83rem">${esc(e.message)}</p></div>`;
    document.getElementById("hdr-count").textContent = "Error";
  }
})();
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/favicon.svg")
def favicon_svg():
    return Response(_FAVICON_SVG, mimetype="image/svg+xml")


@app.route("/favicon.ico")
def favicon_ico():
    return Response(base64.b64decode(_FAVICON_ICO), mimetype="image/x-icon")


@app.route("/favicon.png")
def favicon_png():
    return Response(base64.b64decode(_FAVICON_PNG), mimetype="image/png")


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/fetch", methods=["POST"])
def fetch():
    data      = request.get_json(force=True, silent=True) or {}
    query     = (data.get("query") or "").strip().lower()
    date_from = (data.get("date_from") or "").strip()
    date_to   = (data.get("date_to") or "").strip()

    articles = _get_articles()

    if query:
        articles = [
            a for a in articles
            if query in a["title"].lower() or query in a["summary"].lower()
        ]

    if date_from:
        try:
            ts0 = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc).timestamp()
            articles = [a for a in articles if a["date_ts"] >= ts0]
        except ValueError:
            pass
    if date_to:
        try:
            ts1 = (datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc) + timedelta(days=1)).timestamp()
            articles = [a for a in articles if a["date_ts"] <= ts1]
        except ValueError:
            pass

    articles.sort(key=lambda a: a["date_ts"], reverse=True)
    return jsonify(articles)


@app.route("/quit", methods=["POST"])
def quit_app():
    threading.Thread(target=lambda: (time.sleep(0.4), os._exit(0)), daemon=True).start()
    return "OK"


@app.route("/stopped")
def stopped():
    return (
        '<!DOCTYPE html><html><head><title>9to5AI stopped</title>'
        '<style>body{font-family:-apple-system,sans-serif;background:#111;color:#fff;'
        'display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;}'
        '.logo{font-size:2rem;font-weight:900;font-style:italic;color:#e8363d;margin-bottom:12px;}'
        'p{color:rgba(255,255,255,.45);font-size:.9rem;}</style></head>'
        '<body><div style="text-align:center">'
        '<div class="logo">9to5AI</div>'
        '<p>App has stopped. You can close this tab.</p>'
        '</div></body></html>'
    )


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    global _last_hb
    _last_hb = time.monotonic()
    return "OK"


# ---------------------------------------------------------------------------
# Watchdog — exits when browser tab is closed for > 12 s
# ---------------------------------------------------------------------------

_last_hb: float = time.monotonic()


def _watchdog():
    while True:
        time.sleep(3)
        if time.monotonic() - _last_hb > 12:
            print("[9to5AI] No heartbeat — shutting down.")
            os._exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    threading.Thread(target=_watchdog, daemon=True).start()
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5002")).start()
    app.run(host="0.0.0.0", port=5002, debug=False)
