#!/usr/bin/env python3
"""Search Yelp for businesses by term and location."""

import argparse
import json
import os
import sys
from urllib.parse import urlencode
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
    
    # Fall back to environment variable
    return os.environ.get('YELP_API_KEY')

def search_businesses(term, location=None, latitude=None, longitude=None, 
                     limit=5, sort_by='best_match', price=None):
    """Search for businesses on Yelp."""
    api_key = load_api_key()
    if not api_key:
        print("Error: YELP_API_KEY not found in .env or environment", file=sys.stderr)
        sys.exit(1)
    
    params = {'term': term, 'limit': limit, 'sort_by': sort_by}
    
    if location:
        params['location'] = location
    elif latitude and longitude:
        params['latitude'] = latitude
        params['longitude'] = longitude
    else:
        print("Error: Must provide --location or --latitude/--longitude", file=sys.stderr)
        sys.exit(1)
    
    if price:
        params['price'] = price
    
    url = f"https://api.yelp.com/v3/businesses/search?{urlencode(params)}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.code} - {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    
    return data

def format_hours(hours_data):
    """Format business hours for display."""
    if not hours_data:
        return "Hours not available"
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    hours_list = hours_data[0].get('open', [])
    
    formatted = []
    for entry in hours_list:
        day = days[entry['day']]
        start = f"{entry['start'][:2]}:{entry['start'][2:]}"
        end = f"{entry['end'][:2]}:{entry['end'][2:]}"
        formatted.append(f"{day}: {start}-{end}")
    
    return ', '.join(formatted) if formatted else "Hours not available"

def main():
    parser = argparse.ArgumentParser(description='Search Yelp for businesses')
    parser.add_argument('term', help='Search term (e.g., "dog groomer", "pizza")')
    parser.add_argument('--location', '-l', help='Location (e.g., "San Francisco, CA")')
    parser.add_argument('--latitude', type=float, help='Latitude for location-based search')
    parser.add_argument('--longitude', type=float, help='Longitude for location-based search')
    parser.add_argument('--limit', '-n', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--sort-by', choices=['best_match', 'rating', 'review_count', 'distance'],
                       default='best_match', help='Sort order')
    parser.add_argument('--price', help='Price filter (1,2,3,4 for $-$$$$)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    
    args = parser.parse_args()
    
    data = search_businesses(
        term=args.term,
        location=args.location,
        latitude=args.latitude,
        longitude=args.longitude,
        limit=args.limit,
        sort_by=args.sort_by,
        price=args.price
    )
    
    if args.json:
        print(json.dumps(data, indent=2))
        return
    
    businesses = data.get('businesses', [])
    total = data.get('total', 0)
    
    print(f"Found {total} results for \"{args.term}\"")
    print(f"Showing top {len(businesses)}:\n")
    
    for i, biz in enumerate(businesses, 1):
        name = biz.get('name', 'Unknown')
        rating = biz.get('rating', 'N/A')
        review_count = biz.get('review_count', 0)
        price = biz.get('price', 'N/A')
        phone = biz.get('phone', 'N/A')
        display_phone = biz.get('display_phone', phone)
        
        location = biz.get('location', {})
        address = ', '.join(location.get('display_address', ['Address not available']))
        
        distance = biz.get('distance')
        distance_str = f"{distance/1609.34:.1f} mi" if distance else "N/A"
        
        hours = biz.get('business_hours', [])
        is_open = hours[0].get('is_open_now', False) if hours else None
        open_status = "Open now" if is_open else ("Closed" if is_open is False else "")
        
        categories = ', '.join([c['title'] for c in biz.get('categories', [])])
        
        print(f"[{i}] {name}")
        print(f"    ⭐ {rating} ({review_count} reviews) | {price} | {distance_str}")
        print(f"    📍 {address}")
        print(f"    📞 {display_phone}")
        if open_status:
            print(f"    🕐 {open_status}")
        if categories:
            print(f"    📂 {categories}")
        print()

if __name__ == '__main__':
    main()
