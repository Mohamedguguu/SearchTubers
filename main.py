import json

def scrape_roblox_channels(limit=50):
    """
    Returns mock Roblox YouTube channel data for use in restricted/offline environments.
    """
    print("Running in a restricted environment. Using mock channel data.")
    return [{'channelId': f'UCFAKECHANNEL{i:04}'} for i in range(1, limit + 1)]


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
