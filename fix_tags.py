#!/usr/bin/env python3
"""Fix tags with stricter classification. Rewrites frontmatter in-place."""

import json
import os
import re

BASE_DIR = "/Users/tomasruta/Documents - non iCloud/LaskaObsidian/generalist"
MAPPING_PATH = "/Users/tomasruta/Documents - non iCloud/LaskaObsidian/generalist-url-mapping.json"


def classify_tags(title: str, subtitle: str, content_first_2k: str) -> list:
    """Classify with stricter rules based primarily on title and structure."""
    tags = set()
    title_lower = title.lower()
    sub_lower = subtitle.lower() if subtitle else ""
    text_lower = content_first_2k.lower()

    # --- INTERVIEWS: title-driven ---
    interview_patterns = [
        r'\bthe miss\b', r'\bthe prologue\b', r'\binterview\b',
        r'\bq&a\b', r'\bin conversation\b',
    ]
    # "X on Y" pattern in title (e.g., "Steve Schlafman on Mindful Investing")
    if re.match(r'^[\w\s.\'-]+\bon\b\s+', title) and ':' not in title:
        tags.add("generalist-interviews")
    for p in interview_patterns:
        if re.search(p, title_lower):
            tags.add("generalist-interviews")
            break

    # --- GUIDES: title-driven ---
    guide_patterns = [
        r'\bproductivity stack\b', r'\bhow to\b', r'\bplaybook\b',
        r'\bnostradamus list\b', r'\bpredictions\b', r'\blessons\b',
        r'\bmaster\s*class\b', r'\bguide\b', r'\btips\b',
        r'\bbooks? to read\b', r'\bventure lessons\b',
        r'\bbrunch briefing\b', r'\bin flight\b',
    ]
    for p in guide_patterns:
        if re.search(p, title_lower):
            tags.add("generalist-guides")
            break

    # --- AI: must be a substantial theme, not just mentioned ---
    # Check title first
    ai_title_patterns = [
        r'\bai\b', r'\bartificial intelligence\b', r'\bgpt\b', r'\bllm\b',
        r'\bopenai\b', r'\banthropic\b', r'\bchatgpt\b', r'\bgenerative\b',
        r'\bmachine learning\b', r'\bdeep learning\b', r'\bfoundation model',
        r'\bcopilot\b', r'\bautonomous\b', r'\brobot',
    ]
    ai_in_title = any(re.search(p, title_lower) for p in ai_title_patterns)
    ai_in_subtitle = any(re.search(p, sub_lower) for p in ai_title_patterns)

    if ai_in_title or ai_in_subtitle:
        tags.add("generalist-artificial-intelligence")
    else:
        # Only tag as AI if the content heavily features it (5+ mentions of AI-specific terms)
        ai_mentions = len(re.findall(
            r'\bartificial intelligence\b|\bmachine learning\b|\bdeep learning\b|\bgpt-?\d?\b|\bllm\b|\blarge language model|\bgenerative ai\b|\bfoundation model|\btransformer\b',
            text_lower
        ))
        # Also count standalone "AI" but more carefully (avoid "said", "aim", etc.)
        ai_mentions += len(re.findall(r'\bai\b(?!\w)', text_lower))
        if ai_mentions >= 8:
            tags.add("generalist-artificial-intelligence")

    # --- VENTURE CAPITAL: must be primarily about VC/investing ---
    vc_title_patterns = [
        r'\bventure\b', r'\bvc\b', r'\bipo\b', r'\bs-1\b',
        r'\bfundraising\b', r'\bseed\b.*\bround\b', r'\bseries [a-f]\b',
        r'\bdemo day\b', r'\by combinator\b', r'\bvaluation\b',
    ]
    vc_in_title = any(re.search(p, title_lower) for p in vc_title_patterns)
    if vc_in_title:
        tags.add("generalist-venture-capital")
    else:
        # Check if the article is primarily about investing/VC
        vc_mentions = len(re.findall(
            r'\bventure capital\b|\bvc firms?\b|\bseries [a-f]\b|\bipo\b|\bs-1\b|\braise[ds]?\s+\$|\bfunding round',
            text_lower
        ))
        if vc_mentions >= 5:
            tags.add("generalist-venture-capital")

    # --- CASE STUDIES: deep dives on specific companies ---
    # "Company: Subtitle" title pattern
    if re.match(r'^[\w\s&\.\'-]+:\s+', title):
        # Exclude opinion/briefing/newsletter formats
        if not re.search(r'(opinion|brunch|briefing|in flight|s-1 club|the miss|prologue)', title_lower):
            tags.add("generalist-case-studies")

    # S-1 Club articles
    if 's-1 club' in title_lower:
        tags.add("generalist-case-studies")
        tags.add("generalist-venture-capital")

    # Known company deep dives (company name is the main title subject)
    known_companies = [
        'airbnb', 'stripe', 'shopify', 'doordash', 'notion', 'figma', 'discord',
        'roblox', 'coinbase', 'plaid', 'robinhood', 'palantir', 'snowflake',
        'unity', 'airtable', 'canva', 'databricks', 'nvidia', 'asml',
        'netflix', 'spotify', 'uber', 'lyft', 'twitter', 'snap',
        'anduril', 'scale ai', 'ant group', 'bytedance', 'tiktok',
        'lemonade', 'pexip', 'vroom', 'asana', 'rackspace', 'nintendo',
        'lululemon', 'mercado libre', 'nubank', 'rappi', 'brex',
        'flexport', 'faire', 'rippling', 'a24', 'aave', 'affirm',
        'deel', 'miro', 'linear', 'vercel', 'compound', 'solana',
        'a.team', 'ramp', 'wiz', 'celsius', 'klaviyo',
    ]
    for company in known_companies:
        # Company must appear prominently in title (not just mentioned in passing)
        if re.search(r'\b' + re.escape(company) + r'\b', title_lower):
            tags.add("generalist-case-studies")
            break

    # If still no tags, use content heuristics
    if not tags:
        # Default: most Generalist articles are case studies or analytical essays
        tags.add("generalist-case-studies")

    return sorted(tags)


def main():
    files = sorted([f for f in os.listdir(BASE_DIR) if f.endswith('.md')])
    print(f"Fixing tags for {len(files)} files")

    tag_counts = {}
    processed = 0

    for fname in files:
        filepath = os.path.join(BASE_DIR, fname)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse existing frontmatter
        fm_match = re.match(r'^---\n(.+?)\n---\n\n(.+)', content, re.DOTALL)
        if not fm_match:
            print(f"  No frontmatter in {fname}, skipping")
            continue

        fm_text = fm_match.group(1)
        body = fm_match.group(2)

        # Extract title from frontmatter
        title_m = re.search(r'^title:\s*"(.+?)"', fm_text, re.MULTILINE)
        title = title_m.group(1) if title_m else fname.replace('.md', '')

        # Extract subtitle from body (## line after # title)
        sub_m = re.search(r'^## (.+)$', body, re.MULTILINE)
        subtitle = sub_m.group(1).strip() if sub_m else ""

        # Get first 2000 chars of body for classification
        content_sample = body[:2000]

        # Reclassify
        new_tags = classify_tags(title, subtitle, content_sample)

        for t in new_tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

        # Replace tags line in frontmatter
        tags_str = ', '.join(new_tags)
        new_fm = re.sub(r'^tags: \[.+?\]', f'tags: [{tags_str}]', fm_text, flags=re.MULTILINE)
        new_content = f'---\n{new_fm}\n---\n\n{body}'

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        processed += 1
        if processed % 50 == 0:
            print(f"  Processed {processed}...")

    print(f"\nDone! Fixed {processed} files")
    print("\nTag distribution:")
    for tag, count in sorted(tag_counts.items()):
        print(f"  {tag}: {count}")


if __name__ == '__main__':
    main()
