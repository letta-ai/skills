#!/usr/bin/env python3
"""Fetch Yelp reviews using browser automation."""

import asyncio
import argparse
import os
import sys

# Set up environment for browser-use
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")

async def get_reviews(business_name: str, location: str, num_reviews: int = 5):
    """Get reviews for a business using browser automation."""
    from browser_use import Agent, ChatOpenAI
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Try loading from .env
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.strip().split('=', 1)[1]
                        os.environ["OPENAI_API_KEY"] = api_key
                        break
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found. Set it in environment or .env file.", file=sys.stderr)
        sys.exit(1)
    
    # Use browser-use's ChatOpenAI wrapper
    llm = ChatOpenAI(model="gpt-4o-mini")
    
    task = f"""
    Go to Yelp.com and search for "{business_name}" in "{location}".
    Click on the business in the search results.
    Find and read the reviews section.
    Extract the first {num_reviews} reviews, including:
    - Reviewer name
    - Star rating
    - Date
    - Review text (full text if possible)
    
    Return the reviews in a structured format.
    """
    
    agent = Agent(
        task=task,
        llm=llm,
    )
    
    result = await agent.run()
    return result

def main():
    parser = argparse.ArgumentParser(description='Get Yelp reviews using browser automation')
    parser.add_argument('business', help='Business name to search for')
    parser.add_argument('--location', '-l', default='San Francisco', help='Location (default: San Francisco)')
    parser.add_argument('--num-reviews', '-n', type=int, default=5, help='Number of reviews to fetch (default: 5)')
    
    args = parser.parse_args()
    
    print(f"Fetching reviews for '{args.business}' in {args.location}...")
    print("(This may take a minute as the browser navigates Yelp)\n")
    
    result = asyncio.run(get_reviews(args.business, args.location, args.num_reviews))
    
    print("\n=== Reviews ===\n")
    print(result)

if __name__ == '__main__':
    main()
