import requests
import json
import datetime
import time

API_KEY = "AIzaSyC4KcMWY84RroIbtXTiwo28Md9BU2wdWEI"
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"
PLAYLIST_URL = "https://www.googleapis.com/youtube/v3/playlistItems"

QUERY = "Roblox"
MAX_RESULTS = 50
MIN_SUBS = 1000
DAYS_ACTIVE = 30
OUTPUT_FILE = "players.json"
INTERVAL = 300  # 5 minutes in seconds

def get_recent_channels():
    params = {
        "key": API_KEY,
        "q": QUERY,
        "part": "snippet",
        "type": "channel",
        "maxResults": MAX_RESULTS,
    }
    response = requests.get(SEARCH_URL, params=params)
    return response.json().get("items", [])

def get_channel_details(channel_ids):
    if not channel_ids:
        return []
    params = {
        "key": API_KEY,
        "id": ",".join(channel_ids),
        "part": "snippet,statistics,contentDetails",
        "maxResults": 50,
    }
    response = requests.get(CHANNEL_URL, params=params)
    return response.json().get("items", [])

def get_latest_video_date(uploads_playlist_id):
    params = {
        "key": API_KEY,
        "playlistId": uploads_playlist_id,
        "part": "contentDetails",
        "maxResults": 1,
    }
    response = requests.get(PLAYLIST_URL, params=params)
    items = response.json().get("items", [])
    if not items:
        return None
    return items[0]["contentDetails"]["videoPublishedAt"]

def is_recent(published_at_str):
    published_at = datetime.datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
    return (datetime.datetime.utcnow() - published_at).days <= DAYS_ACTIVE

def load_existing():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main_cycle():
    raw_channels = get_recent_channels()
    channel_ids = [item["snippet"]["channelId"] for item in raw_channels]
    details = get_channel_details(channel_ids)

    result = {}
    for ch in details:
        try:
            subs = int(ch["statistics"].get("subscriberCount", "0"))
            if subs < MIN_SUBS:
                continue

            lang = ch["snippet"].get("defaultLanguage", "en").lower()
            if lang not in ["en", "en-us", "en-gb", None]:
                continue

            uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
            latest_date = get_latest_video_date(uploads_id)
            if not latest_date or not is_recent(latest_date):
                continue

            cid = ch["id"]
            result[cid] = {
                "channelId": cid,
                "title": ch["snippet"]["title"],
                "publishedAt": ch["snippet"]["publishedAt"],
                "subscriberCount": subs,
                "lastUpload": latest_date,
                "defaultLanguage": lang,
            }
        except Exception as e:
            print(f"Error processing channel: {e}")

    save_data(result)
    print(f"[{datetime.datetime.now()}] Saved {len(result)} active Roblox YouTubers to {OUTPUT_FILE}")

if __name__ == "__main__":
    while True:
        start = time.time()
        try:
            main_cycle()
        except Exception as err:
            print("Error in cycle:", err)
        elapsed = time.time() - start
        wait_time = INTERVAL - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
