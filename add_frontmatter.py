#!/usr/bin/env python3
"""Add YAML frontmatter, classify tags, and rename files for Obsidian."""

import json
import os
import re
from datetime import datetime

BASE_DIR = "/Users/tomasruta/Documents - non iCloud/LaskaObsidian/generalist"
JSON_PATH = "/Users/tomasruta/Downloads/substack-premium-scraper/data/generalist.json"
MAPPING_PATH = "/Users/tomasruta/Documents - non iCloud/LaskaObsidian/generalist-url-mapping.json"

# Keywords for tag classification
TAG_RULES = {
    "generalist-artificial-intelligence": [
        r'\bai\b', r'\bartificial intelligence\b', r'\bmachine learning\b', r'\bdeep learning\b',
        r'\bgpt\b', r'\bllm\b', r'\blarge language model', r'\bneural net', r'\bopenai\b',
        r'\banthropic\b', r'\bchatgpt\b', r'\bgenerative ai\b', r'\bfoundation model',
        r'\btransformer\b', r'\bcomputer vision\b', r'\bnlp\b', r'\bnatural language\b',
        r'\bmidjourney\b', r'\bstable diffusion\b', r'\bautonomous\b', r'\brobot',
        r'\bcopilot\b', r'\bgemini\b', r'\bclaude\b', r'\bhugging\s*face\b',
    ],
    "generalist-venture-capital": [
        r'\bventure capital\b', r'\bvc\b', r'\bfundraising\b', r'\bseries [a-f]\b',
        r'\bseed round\b', r'\bipo\b', r'\bs-1\b', r'\bvaluation\b', r'\bfunding\b',
        r'\binvestor\b', r'\binvesting\b', r'\bstartup\b', r'\bstart-up\b',
        r'\bsequoia\b', r'\ba16z\b', r'\bandreessen\b', r'\bbenchmark\b',
        r'\bfounders fund\b', r'\baccel\b', r'\bfund\b', r'\bgrowth stage\b',
        r'\bearly stage\b', r'\bunicorn\b', r'\bdemo day\b', r'\by combinator\b',
        r'\bangel\b', r'\bpre-seed\b', r'\braise\b.*\bmillion\b',
    ],
    "generalist-case-studies": [
        # Detected by structure: deep dives on specific companies
    ],
    "generalist-interviews": [
        r'\binterview\b', r'\bprologue\b', r'\bthe miss\b', r'\bconversation with\b',
        r'\bspeaks with\b', r'\btalks to\b', r'\bsat down with\b', r'\bq&a\b',
        r'\bwe (spoke|talked|chatted)\b', r'\bi (spoke|talked|chatted) (with|to)\b',
    ],
    "generalist-guides": [
        r'\bhow to\b', r'\bguide\b', r'\bplaybook\b', r'\bframework\b',
        r'\blessons\b', r'\btips\b', r'\bproductivity\b', r'\bstack\b',
        r'\bstrateg(y|ies)\b', r'\btactics\b', r'\bprinciples\b', r'\bmaster class\b',
        r'\bnostradamus list\b', r'\bpredictions\b',
    ],
}

# Company deep-dive patterns for case-studies tag
COMPANY_PATTERNS = [
    # Title patterns like "CompanyName: Subtitle" or "The Story of CompanyName"
    r'^#\s+\w[\w\s]*:\s+',  # "Company: Subtitle"
]

# Known company names that indicate case studies when they're the main subject
KNOWN_COMPANIES = [
    'airbnb', 'stripe', 'shopify', 'doordash', 'notion', 'figma', 'discord',
    'roblox', 'coinbase', 'plaid', 'robinhood', 'palantir', 'snowflake',
    'unity', 'airtable', 'canva', 'databricks', 'gitlab', 'nvidia',
    'microsoft', 'google', 'amazon', 'apple', 'meta', 'facebook', 'netflix',
    'spotify', 'uber', 'lyft', 'twitter', 'snap', 'pinterest', 'reddit',
    'slack', 'zoom', 'twilio', 'cloudflare', 'crowdstrike', 'datadog',
    'mongodb', 'elastic', 'confluent', 'hashicorp', 'gitlab',
    'anduril', 'scale ai', 'hugging face', 'stability ai', 'cohere',
    'mistral', 'perplexity', 'ant group', 'bytedance', 'tiktok',
    'lemonade', 'pexip', 'vroom', 'asana', 'rackspace', 'nintendo',
    'lululemon', 'mercado libre', 'nubank', 'rappi', 'brex',
    'flexport', 'faire', 'rippling', 'gusto', 'deel', 'remote',
    'linear', 'vercel', 'supabase', 'retool', 'miro', 'clickup',
]


def sanitize_filename(title: str) -> str:
    """Convert a title to a filesystem-safe filename."""
    # Remove or replace problematic characters
    name = title.strip()
    # Replace characters not allowed in filenames
    name = re.sub(r'[/\\:*?"<>|]', '-', name)
    # Replace multiple spaces/dashes with single dash
    name = re.sub(r'[\s]+', ' ', name)
    # Remove leading/trailing dots and spaces
    name = name.strip('. ')
    # Truncate to reasonable length (200 chars max for filesystem safety)
    if len(name) > 200:
        name = name[:200].rsplit(' ', 1)[0]
    return name


def parse_date(date_str: str) -> str:
    """Convert date string like 'Jan 22, 2026' to '2026-01-22'."""
    formats = [
        "%b %d, %Y",   # Jan 22, 2026
        "%B %d, %Y",   # January 22, 2026
        "%Y-%m-%d",    # Already formatted
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str  # Return as-is if parsing fails


def classify_tags(title: str, content: str) -> list:
    """Classify article into tags based on content analysis."""
    tags = set()
    text_lower = content.lower()
    title_lower = title.lower()

    # Check keyword-based tags
    for tag, patterns in TAG_RULES.items():
        if tag == "generalist-case-studies":
            continue  # Handled separately
        for pattern in patterns:
            if re.search(pattern, text_lower):
                tags.add(tag)
                break

    # Case studies detection
    # 1. Title has "Company: Subtitle" pattern
    if re.match(r'^[\w\s&\'-]+:\s+', title) and not title.lower().startswith(('opinion', 'brunch', 'in flight')):
        tags.add("generalist-case-studies")

    # 2. Title features a known company prominently
    for company in KNOWN_COMPANIES:
        if company.lower() in title_lower:
            tags.add("generalist-case-studies")
            break

    # 3. S-1 Club articles are case studies
    if 's-1 club' in title_lower or 's-1 club' in text_lower[:500]:
        tags.add("generalist-case-studies")

    # Interview detection from title patterns
    interview_title_patterns = [
        r'the miss\b', r'the prologue\b', r'\binterview\b', r'\bq&a\b',
        r'on building\b', r'on investing\b', r'on snagging\b',
    ]
    for pattern in interview_title_patterns:
        if re.search(pattern, title_lower):
            tags.add("generalist-interviews")
            break

    # Brunch briefings are guides/newsletters
    if 'brunch briefing' in title_lower:
        tags.add("generalist-guides")

    # If no tags matched, default to case-studies (most Generalist content is deep dives)
    if not tags:
        # Check if it reads like an analytical piece about a company/industry
        tags.add("generalist-case-studies")

    return sorted(tags)


def process_file(filepath: str, metadata: dict) -> tuple:
    """Process a single markdown file. Returns (old_name, new_name, success)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title from first H1
    title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else metadata.get('title', 'Untitled')
    # Clean up bold markers in title
    title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)

    # Get date from metadata (already extracted during scraping)
    date_str = metadata.get('date', 'Date not found')
    date_iso = parse_date(date_str)

    # Classify tags
    tags = classify_tags(title, content)

    # Build frontmatter
    # Escape quotes in title for YAML
    yaml_title = title.replace('"', '\\"')
    tags_str = ', '.join(tags)
    frontmatter = f'---\ntitle: "{yaml_title}"\ndate: {date_iso}\nauthor: "Mario Gabriele"\ntags: [{tags_str}]\n---\n\n'

    # Prepend frontmatter (skip if already has frontmatter)
    if content.startswith('---\n'):
        return os.path.basename(filepath), os.path.basename(filepath), False

    new_content = frontmatter + content

    # Write updated content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # Generate new filename
    new_name = sanitize_filename(title) + '.md'
    old_name = os.path.basename(filepath)

    if new_name != old_name:
        new_path = os.path.join(os.path.dirname(filepath), new_name)
        # Handle collisions
        if os.path.exists(new_path) and new_path != filepath:
            base, ext = os.path.splitext(new_name)
            counter = 2
            while os.path.exists(os.path.join(os.path.dirname(filepath), f"{base} ({counter}){ext}")):
                counter += 1
            new_name = f"{base} ({counter}){ext}"
            new_path = os.path.join(os.path.dirname(filepath), new_name)
        os.rename(filepath, new_path)

    return old_name, new_name, True


def main():
    # Load metadata
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        all_metadata = json.load(f)

    # Build lookup by filename
    meta_by_file = {}
    for m in all_metadata:
        fname = os.path.basename(m['file_link'])
        meta_by_file[fname] = m

    # Get all markdown files
    md_files = sorted([f for f in os.listdir(BASE_DIR) if f.endswith('.md')])
    print(f"Found {len(md_files)} markdown files to process")

    mapping = []
    processed = 0
    skipped = 0
    errors = 0

    for fname in md_files:
        filepath = os.path.join(BASE_DIR, fname)
        metadata = meta_by_file.get(fname, {})

        # Reconstruct original URL from slug
        slug = fname.replace('.md', '')
        original_url = f"https://www.generalist.com/p/{slug}"

        try:
            old_name, new_name, success = process_file(filepath, metadata)
            if success:
                processed += 1
                mapping.append({
                    "old_filename": old_name,
                    "new_filename": new_name,
                    "original_url": original_url,
                })
                if processed % 50 == 0:
                    print(f"  Processed {processed} files...")
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            print(f"  Error processing {fname}: {e}")
            mapping.append({
                "old_filename": fname,
                "new_filename": fname,
                "original_url": original_url,
                "error": str(e),
            })

    # Save mapping file
    with open(MAPPING_PATH, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\nDone!")
    print(f"  Processed: {processed}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Mapping saved to: {MAPPING_PATH}")


if __name__ == '__main__':
    main()
