#!/usr/bin/env python3
"""Search Yelp for a business by phone number."""

import argparse
import json
import os
import sys
import urllib.request

def load_api_key():
    """Load API key from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    env_path = os.path.abspath(env_path)
    
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('YELP_API_KEY='):
                    return line.strip().split('=', 1)[1]
    
    return os.environ.get('YELP_API_KEY')

def search_by_phone(phone):
    """Search for a business by phone number."""
    api_key = load_api_key()
    if not api_key:
        print("Error: YELP_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    
    # Ensure phone is in E.164 format
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if not phone.startswith('+'):
        phone = '+1' + phone  # Assume US if no country code
    
    url = f"https://api.yelp.com/v3/businesses/search/phone?phone={phone}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.code} - {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Search Yelp by phone number')
    parser.add_argument('phone', help='Phone number (e.g., +14155551234)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    
    args = parser.parse_args()
    
    data = search_by_phone(args.phone)
    
    if args.json:
        print(json.dumps(data, indent=2))
        return
    
    businesses = data.get('businesses', [])
    
    if not businesses:
        print(f"No business found for phone: {args.phone}")
        return
    
    print(f"Found {len(businesses)} business(es) for {args.phone}:\n")
    
    for biz in businesses:
        name = biz.get('name', 'Unknown')
        rating = biz.get('rating', 'N/A')
        review_count = biz.get('review_count', 0)
        
        location = biz.get('location', {})
        address = ', '.join(location.get('display_address', ['N/A']))
        
        categories = ', '.join([c['title'] for c in biz.get('categories', [])])
        
        print(f"📍 {name}")
        print(f"   ⭐ {rating} ({review_count} reviews)")
        print(f"   📍 {address}")
        print(f"   📂 {categories}")
        print(f"   🔗 {biz.get('url', 'N/A')}")
        print()

if __name__ == '__main__':
    main()
