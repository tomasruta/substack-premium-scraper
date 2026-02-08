# SESSION LOG: substack-premium-scraper

## Session 0 — 2026-02-01 (~1 hr 48 min)
_This session was run from `~/Downloads/Substack2Markdown-chrome/` (the original fork) but all work happened on files in `~/Downloads/substack-premium-scraper/`. No git commits were made — code sat in Downloads for 6 days._

**Built:** Complete Substack scraper that bypasses paywall using cookie authentication, with frontmatter generation and tag classification

### Goal
Scrape 373 paid articles from The Generalist (generalist.com) Substack to markdown, output to Obsidian vault at `/Users/tomasruta/Documents - non iCloud/LaskaObsidian/generalist/`.

### What happened

**1. Tried fixing the Camoufox browser scraper — abandoned:**
- Started with a broken `substack_scraper.py` using Camoufox (headless browser)
- Fixed CSS selectors in `extract_post_data()` — tested with 1 article, got "Untitled" and "Date not found"
- Inspected HTML — page content was garbled/binary from Camoufox (content-encoding/decompression issue)
- **Key insight:** Substack serves fully server-rendered HTML — no browser needed at all

**2. Rewrote with `requests` + cookie authentication:**
- Created `CookieSubstackScraper` class using Python `requests` + Netscape cookie file
- Extracted dates from JSON-LD structured data (`datePublished`) instead of CSS selectors
- Verified paywall bypass: 25,435 chars authenticated vs 997 chars unauthenticated (25.5x ratio)

**3. Full scrape:**
- 373 articles scraped at ~1.5 articles/second (~4 minutes total)
- All output to Obsidian vault

**4. Frontmatter generation (`add_frontmatter.py`):**
- Adds YAML frontmatter: title, date, author, tags
- Renames files from URL slugs to actual article titles
- Classifies tags based on content keywords

**5. Tag classification iteration (`fix_tags.py`):**
- First pass was too loose — `generalist-guides` hit 347/373 articles
- Built separate `fix_tags.py` with stricter rules + exclusion patterns
- Final distribution: case-studies (266), guides (71), AI (36), VC (22), interviews (15)

**6. Fixed 32 podcast episodes with generic titles:**
- Podcast episodes had "The Generalist" as H1 (show name, not episode title)
- First tried extracting from URL slugs — approximate
- Then re-fetched pages using cookies and got proper titles from `og:title` metadata
- Added `generalist-podcast` tag to all 32

### Key decisions
| Decision | Why |
|----------|-----|
| `requests` over Camoufox | Substack serves server-rendered HTML. No JS rendering needed. 100x faster, more reliable |
| JSON-LD for dates | CSS selectors break when Substack changes class names. JSON-LD `datePublished` is stable (SEO) |
| `og:title` for podcast titles | URL slugs give approximate titles; `og:title` has full formatted titles with guest names |
| Two-pass tag classification | First pass too broad. Separate `fix_tags.py` allows iterative refinement without re-running full pipeline |
| Cookie file auth | Simple, effective. Export cookies once from browser, scraper uses them directly |

### Dead ends
1. **Camoufox browser scraper** — returned garbled binary content (content-encoding issue)
2. **Edge scraper (`~/Downloads/Substack2Markdown`)** — couldn't persist authenticated sessions
3. **Chrome scraper (`~/Downloads/Substack2Markdown-chrome`)** — ChromeDriver version mismatch
4. **First-pass tag keywords** — too loose, almost everything matched multiple tags
5. **Cookie file temporarily lost** — user had trashed it mid-session, worked around with URL slugs, then re-fetched when restored

### Files created
- `substack_scraper.py` — main scraper with `CookieSubstackScraper` class
- `add_frontmatter.py` — YAML frontmatter generation and file renaming
- `fix_tags.py` — stricter tag classification
- `CLAUDE.md` — project instructions and workflow

---

## Session 1 — 2026-02-07 (~4 min)
**Task:** Repo ownership transfer

**What happened:**
- Repo was cloned from `yowmamasita/substack-premium-scraper` — remote pointed to their GitHub
- Created new repo `tomasruta/substack-premium-scraper` on GitHub (public)
- Changed git remote to own account
- Staged and committed 4 files: `CLAUDE.md`, `add_frontmatter.py`, `fix_tags.py`, `substack_scraper.py`
- Pushed to new repo

**Commit:** `feat: add frontmatter tools and project docs` (`2bf22af`)

---

## Lessons from Substack2Markdown-chrome fork

Before creating `substack-premium-scraper`, three different browser-based approaches were tried from forks/downloads. All failed. Key takeaways:

1. **Browser-based scraping is unnecessary for Substack.** Substack serves fully server-rendered HTML. `requests` with cookie auth is faster, simpler, and more reliable than any browser automation. Three different browser approaches all failed for different reasons.

2. **Cookie files expire.** Should be kept in a known location. Scraper should fail gracefully with a clear message when cookies are invalid/missing.

3. **CSS selectors break; structured data doesn't.** Substack changes `.pencraft` class names regularly. Use JSON-LD `datePublished` for dates and `og:title` for titles — stable because Substack needs them for SEO/social sharing.

4. **Podcast/audio episodes have different HTML structure.** The H1 is the show name, not the episode title. Episode title is only in `og:title` metadata. Any scraper needs to handle this edge case.

5. **Tag classification needs iteration.** Broad keyword matching produces useless tags. Stricter rules with exclusion patterns and context-aware matching work better. Build as a separate script for quick iteration.

6. **All development history is only in the JSONL session file.** The code sat in `~/Downloads/` for 6 days with no version control. The 5+ edits to `substack_scraper.py` and creation of 2 new scripts have no git trail.

---
