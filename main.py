import json
import re
import requests

# This script scrapes YouTube search results for "Roblox" channels using raw HTML (limited by YouTube's client-side rendering).

SEARCH_URL = "https://www.youtube.com/results"


def scrape_roblox_channels(limit=50):
    """
    Attempts to scrape YouTube search results for "Roblox" and extracts up to `limit` channel IDs.
    Returns a list of dicts with 'channelId'.
    Note: May fail due to YouTube dynamic content. Best used in environments where Selenium isn't available.
    """
    params = {
        'search_query': 'roblox'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }

    try:
        response = requests.get(SEARCH_URL, params=params, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch YouTube search page: {e}")
        return []

    html = response.text
    channel_ids = re.findall(r'/channel/(UC[0-9A-Za-z_-]{20,})', html)

    seen = set()
    unique_ids = []
    for cid in channel_ids:
        if cid not in seen:
            seen.add(cid)
            unique_ids.append(cid)
        if len(unique_ids) >= limit:
            break

    return [{'channelId': cid} for cid in unique_ids]


def save_to_json(data, filename='players.json'):
    """
    Saves the given data (list of dicts) to a JSON file. If the file exists, it will be overwritten.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {filename}")


if __name__ == '__main__':
    roblox_channels = scrape_roblox_channels(limit=50)
    if not roblox_channels:
        print("No channels found or an error occurred.")
    else:
        print(f"Found {len(roblox_channels)} channel IDs:")
        for c in roblox_channels:
            print(c['channelId'])
    save_to_json(roblox_channels)

