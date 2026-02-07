# Substack Premium Scraper

## What This Does
Scrapes paid Substack articles to markdown files using cookies for authentication. No browser needed - uses Python `requests` with Netscape cookie files.

## How To Scrape a Substack

### 1. Export cookies
Use a browser extension (e.g., "Get cookies.txt LOCALLY") to export cookies from the Substack you're subscribed to. Save as Netscape format .txt file.

### 2. Run the scraper
```bash
source venv/bin/activate
python substack_scraper.py \
  --url https://www.THE-SUBSTACK.com \
  --premium \
  --cookie-file ~/Downloads/www.THE-SUBSTACK.com_cookies.txt \
  -d "/Users/tomasruta/Documents - non iCloud/LaskaObsidian"
```

### 3. Add frontmatter and rename files
Edit `add_frontmatter.py` to update:
- `BASE_DIR` - point to the new output directory
- `JSON_PATH` - point to the new JSON metadata file
- Author name in the `classify_tags` function and frontmatter template
- Tag categories if the new Substack has different themes

Then run:
```bash
python add_frontmatter.py
```

Optionally run `fix_tags.py` afterward if tag classification needs tightening.

## Key Files
- `substack_scraper.py` - Main scraper. Uses `CookieSubstackScraper` class (requests-based, fast) not the old `PremiumSubstackScraper` (Camoufox browser-based, broken).
- `add_frontmatter.py` - Adds YAML frontmatter, renames files from URL slugs to titles, classifies tags.
- `fix_tags.py` - Retags files with stricter classification rules.

## Important Notes
- The Camoufox/browser approach doesn't work (returns garbled content). Always use the cookie-based approach.
- Cookie files expire. If scraping fails with paywall errors, re-export cookies from your browser.
- The scraper skips files that already exist, so it's safe to re-run if interrupted.
- Output goes to Obsidian vault at: /Users/tomasruta/Documents - non iCloud/LaskaObsidian/
