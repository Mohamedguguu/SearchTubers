import json
import datetime
import time
from googleapiclient.discovery import build

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────
API_KEY = "AIzaSyC4KcMWY84RroIbtXTiwo28Md9BU2wdWEI"
SEARCH_QUERY = "Roblox"
MIN_SUBSCRIBERS = 1000
# Consider a channel "active" if they uploaded in the last 30 days
ACTIVE_DAYS_THRESHOLD = 30
OUTPUT_FILE = "players.json"
MAX_RESULTS = 50      # Number of search results per page (max 50)

# How often (in seconds) to re‐run the search & update.
# 86400 seconds = 24 hours. Change as needed.
UPDATE_INTERVAL_SECONDS = 86400

# ─── SET UP YOUTUBE CLIENT ───────────────────────────────────────────────────────
youtube = build("youtube", "v3", developerKey=API_KEY)

# ─── HELPERS ─────────────────────────────────────────────────────────────────────
def load_existing_players():
    """Load existing players from OUTPUT_FILE (or return empty dict)."""
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}

def save_players(players_dict):
    """Save the players dict back to OUTPUT_FILE."""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(players_dict, f, indent=2, ensure_ascii=False)
    print(f"[{datetime.datetime.utcnow().isoformat()}] Saved {len(players_dict)} channels to '{OUTPUT_FILE}'")

def channel_active_within_threshold(published_at):
    """Check if a given ISO date string is within ACTIVE_DAYS_THRESHOLD days from today."""
    # YouTube returns timestamps like "2025-05-15T12:34:56Z"
    last_upload = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    now = datetime.datetime.utcnow()
    return (now - last_upload).days <= ACTIVE_DAYS_THRESHOLD

# ─── CORE UPDATE FUNCTION ────────────────────────────────────────────────────────
def update_players_file():
    existing_players = {}

    # Step 1: Search for channels matching SEARCH_QUERY
    search_response = youtube.search().list(
        q=SEARCH_QUERY,
        type="channel",
        part="snippet",
        maxResults=MAX_RESULTS
    ).execute()

    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        snippet = item["snippet"]

        # If defaultLanguage is present, require English; otherwise assume English
        default_language = snippet.get("defaultLanguage", "en")
        if default_language.lower() not in ("en", "en_us", "en-gb", "en"):
            continue

        # Step 2: Fetch channel statistics & content details
        stats_response = youtube.channels().list(
            id=channel_id,
            part="snippet,statistics,contentDetails"
        ).execute()
        info_items = stats_response.get("items", [])
        if not info_items:
            continue

        info = info_items[0]
        stats = info["statistics"]
        content_details = info["contentDetails"]

        # Filter by subscriber count
        subscriber_count = int(stats.get("subscriberCount", 0))
        if subscriber_count < MIN_SUBSCRIBERS:
            continue

        # Step 3: Check recent upload (use the "uploads" playlist)
        uploads_playlist_id = content_details["relatedPlaylists"]["uploads"]
        playlist_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="contentDetails",
            maxResults=1
        ).execute()
        videos = playlist_response.get("items", [])
        if not videos:
            continue

        last_video_info = videos[0]["contentDetails"]
        published_at = last_video_info["videoPublishedAt"]
        if not channel_active_within_threshold(published_at):
            continue

        # Channel matches all criteria → collect data
        channel_data = {
            "channelId": channel_id,
            "title": snippet["title"],
            "description": snippet.get("description", ""),
            "publishedAt": snippet["publishedAt"],
            "subscriberCount": subscriber_count,
            "country": snippet.get("country", ""),
            "defaultLanguage": default_language,
            "lastUploadDate": published_at
        }
        existing_players[channel_id] = channel_data

    # Step 4: Overwrite OUTPUT_FILE with the filtered channels
    save_players(existing_players)

# ─── ENTRY POINT ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[{datetime.datetime.utcnow().isoformat()}] Starting auto‐update loop, interval = {UPDATE_INTERVAL_SECONDS} seconds.")
    while True:
        try:
            update_players_file()
        except Exception as e:
            # If something goes wrong, print the error but keep looping.
            print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR during update: {e}")
        # Sleep until the next run
        time.sleep(UPDATE_INTERVAL_SECONDS)
