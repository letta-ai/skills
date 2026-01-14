#!/usr/bin/env python3
"""Get detailed information about a Yelp business."""

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

def get_business_details(business_id):
    """Get detailed business information."""
    api_key = load_api_key()
    if not api_key:
        print("Error: YELP_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    
    url = f"https://api.yelp.com/v3/businesses/{business_id}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.code} - {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

def format_hours(hours_data):
    """Format business hours."""
    if not hours_data:
        return []
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hours_list = hours_data[0].get('open', [])
    
    # Group by day
    day_hours = {i: [] for i in range(7)}
    for entry in hours_list:
        day_hours[entry['day']].append(entry)
    
    formatted = []
    for day_num, entries in day_hours.items():
        if entries:
            times = []
            for e in entries:
                start = f"{e['start'][:2]}:{e['start'][2:]}"
                end = f"{e['end'][:2]}:{e['end'][2:]}"
                times.append(f"{start}-{end}")
            formatted.append(f"{days[day_num]}: {', '.join(times)}")
        else:
            formatted.append(f"{days[day_num]}: Closed")
    
    return formatted

def main():
    parser = argparse.ArgumentParser(description='Get Yelp business details')
    parser.add_argument('business_id', help='Business ID or alias')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    
    args = parser.parse_args()
    
    data = get_business_details(args.business_id)
    
    if args.json:
        print(json.dumps(data, indent=2))
        return
    
    print(f"=== {data.get('name', 'Unknown')} ===\n")
    
    print(f"⭐ Rating: {data.get('rating', 'N/A')} ({data.get('review_count', 0)} reviews)")
    print(f"💰 Price: {data.get('price', 'N/A')}")
    print(f"📞 Phone: {data.get('display_phone', data.get('phone', 'N/A'))}")
    
    location = data.get('location', {})
    address = '\n         '.join(location.get('display_address', ['N/A']))
    print(f"📍 Address: {address}")
    
    if location.get('cross_streets'):
        print(f"   Cross streets: {location['cross_streets']}")
    
    categories = ', '.join([c['title'] for c in data.get('categories', [])])
    print(f"📂 Categories: {categories}")
    
    hours = data.get('hours', [])
    if hours:
        is_open = hours[0].get('is_open_now', False)
        print(f"\n🕐 Currently: {'Open' if is_open else 'Closed'}")
        print("\nHours:")
        for line in format_hours(hours):
            print(f"  {line}")
    
    print(f"\n🔗 Yelp URL: {data.get('url', 'N/A')}")

if __name__ == '__main__':
    main()
