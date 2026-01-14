#!/usr/bin/env python3
"""Scrape Yelp reviews using Browserbase (handles CAPTCHA with proxies)."""

import argparse
import json
import os
import sys

def load_env():
    """Load environment variables from .env file."""
    # Try multiple paths
    for env_path in [
        os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'),
        os.path.join(os.getcwd(), '.env'),
    ]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            return True
    return False

def scrape_reviews(url: str, num_reviews: int = 5):
    """Scrape reviews from a Yelp business page using Browserbase."""
    from playwright.sync_api import sync_playwright
    from browserbase import Browserbase
    
    load_env()
    
    api_key = os.environ.get("BROWSERBASE_API_KEY")
    project_id = os.environ.get("BROWSERBASE_PROJECT_ID")
    
    if not api_key or not project_id:
        print("Error: BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID required", file=sys.stderr)
        return None
    
    bb = Browserbase(api_key=api_key)
    
    with sync_playwright() as p:
        print("Creating Browserbase session with proxies...", file=sys.stderr)
        session = bb.sessions.create(
            project_id=project_id,
            proxies=True
        )
        
        browser = p.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]
        
        try:
            print(f"Loading {url}...", file=sys.stderr)
            page.goto(url, timeout=45000)
            page.wait_for_timeout(3000)
            
            # Extract business name
            name = "Unknown"
            h1 = page.locator("h1")
            if h1.count() > 0:
                name = h1.first.text_content() or "Unknown"
            
            # Extract rating
            rating = None
            rating_el = page.locator("[aria-label*='star rating']")
            if rating_el.count() > 0:
                rating = rating_el.first.get_attribute("aria-label")
            
            # Extract reviews
            reviews = []
            seen_texts = set()
            
            # Try p[class*='comment'] first
            review_els = page.locator("p[class*='comment']")
            count = review_els.count()
            
            for i in range(count):
                if len(reviews) >= num_reviews:
                    break
                try:
                    text = review_els.nth(i).text_content()
                    if text and len(text) > 50:
                        text_key = text[:100]
                        if text_key not in seen_texts:
                            seen_texts.add(text_key)
                            reviews.append({"text": text.strip()})
                except:
                    continue
            
            print(f"Extracted {len(reviews)} reviews", file=sys.stderr)
            
        finally:
            browser.close()
            print(f"Session: https://browserbase.com/sessions/{session.id}", file=sys.stderr)
        
        return {"business": name.strip(), "rating": rating, "reviews": reviews}

def main():
    parser = argparse.ArgumentParser(description='Scrape Yelp reviews via Browserbase')
    parser.add_argument('url', help='Yelp business URL')
    parser.add_argument('--num-reviews', '-n', type=int, default=5)
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    result = scrape_reviews(args.url, args.num_reviews)
    
    if not result:
        sys.exit(1)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n=== {result['business']} ===")
        if result['rating']:
            print(f"Rating: {result['rating']}")
        print()
        for i, review in enumerate(result['reviews'], 1):
            text = review['text']
            if len(text) > 300:
                text = text[:300] + "..."
            print(f"[{i}] {text}\n")

if __name__ == '__main__':
    main()
