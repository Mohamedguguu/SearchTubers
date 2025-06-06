# File: main.py
import os
import json
import sys
import requests

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

def scrape_roblox_channels(limit=50):
    """
    Fetches up to `limit` Roblox-related YouTube channel IDs using the YouTube Data API.
    If YT_API_KEY is missing or any error occurs, returns a mock list instead.
    """
    api_key = "AIzaSyDiXNnOTJJeuzh-Vn2PH1ZY7AcdRLprgK4"
    if not api_key:
        print("⚠️  YT_API_KEY not set. Falling back to mock channel data.")
        return [{'channelId': f'UCFAKECHANNEL{i:04}'} for i in range(1, limit + 1)]

    params = {
        'key': api_key,
        'part': 'snippet',
        'q': 'roblox',
        'type': 'channel',
        'maxResults': min(limit, 50)
    }

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = data.get('items', [])
        channel_ids = []

        for item in items:
            cid = item.get('id', {}).get('channelId')
            if cid:
                channel_ids.append(cid)
            if len(channel_ids) >= limit:
                break

        if not channel_ids:
            print("⚠️  YouTube API returned no channels. Using mock data.")
            return [{'channelId': f'UCFAKECHANNEL{i:04}'} for i in range(1, limit + 1)]

        print(f"✅  Fetched {len(channel_ids)} real channel IDs from YouTube.")
        return [{'channelId': cid} for cid in channel_ids]

    except Exception as e:
        print(f"⚠️  YouTube API request failed: {e}")
        print("    Falling back to mock channel data.")
        return [{'channelId': f'UCFAKECHANNEL{i:04}'} for i in range(1, limit + 1)]


def save_to_json(data, filename='players.json'):
    """
    Saves the given list of dicts to a JSON file (overwrites if existing).
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅  Saved {len(data)} entries to {filename}")


def main():
    # Allow an optional command-line argument for "limit"; default is 50.
    limit = 50
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print("⚠️  Invalid limit argument; using default of 50.")

    roblox_channels = scrape_roblox_channels(limit=limit)
    if not roblox_channels:
        print("⚠️  No channels found or an error occurred—creating empty players.json.")
        roblox_channels = []

    print(f"Found {len(roblox_channels)} channel IDs:")
    for c in roblox_channels:
        print("  •", c['channelId'])

    save_to_json(roblox_channels)


if __name__ == '__main__':
    main()
