
import json
import datetime
from googleapiclient.discovery import build

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────
API_KEY = "AIzaSyC4KcMWY84RroIbtXTiwo28Md9BU2wdWEI"
SEARCH_QUERY = "Roblox"
MIN_SUBSCRIBERS = 1000
# Consider a channel "active" if they uploaded in the last 30 days
ACTIVE_DAYS_THRESHOLD = 30
OUTPUT_FILE = "players.json"
MAX_RESULTS = 50  # Number of search results per page (max 50)

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
    print(f"Saved {len(players_dict)} channels to '{OUTPUT_FILE}'")

def channel_active_within_threshold(published_at):
    """Check if a given ISO date string is within ACTIVE_DAYS_THRESHOLD days from today."""
    last_upload = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    now = datetime.datetime.utcnow()
    return (now - last_upload).days <= ACTIVE_DAYS_THRESHOLD

# ─── MAIN LOGIC ─────────────────────────────────────────────────────────────────
def main():
    existing_players = load_existing_players()

    # Step 1: Search for channels with the query "Roblox"
    search_response = youtube.search().list(
        q=SEARCH_QUERY,
        type="channel",
        part="snippet",
        maxResults=MAX_RESULTS
    ).execute()

    for item in search_response.get("items", []):
        channel_id = item["snippet"]["channelId"]
        channel_snippet = item["snippet"]

        # Optional: Check defaultLanguage; if missing, assume English
        default_language = channel_snippet.get("defaultLanguage", "en")
        if default_language.lower() not in ("en", "en_us", "en-gb"):
            continue

        # Step 2: Fetch channel statistics and content details
        stats_response = youtube.channels().list(
            id=channel_id,
            part="snippet,statistics,contentDetails"
        ).execute()

        channel_info = stats_response.get("items", [])
        if not channel_info:
            continue

        info = channel_info[0]
        stats = info["statistics"]
        snippet = info["snippet"]
        content_details = info["contentDetails"]

        subscriber_count = int(stats.get("subscriberCount", 0))
        if subscriber_count < MIN_SUBSCRIBERS:
            continue

        # Step 3: Check if channel has any recent upload
        # Fetch the uploads playlist ID
        uploads_playlist_id = content_details["relatedPlaylists"]["uploads"]

        # Get the most recent video from the uploads playlist
        playlist_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="contentDetails",
            maxResults=1
        ).execute()

        videos = playlist_response.get("items", [])
        if not videos:
            continue

        most_recent_video = videos[0]["contentDetails"]
        published_at = most_recent_video["videoPublishedAt"]
        if not channel_active_within_threshold(published_at):
            continue

        # At this point, channel matches criteria
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

    # Step 4: Save to players.json
    save_players(existing_players)


if __name__ == "__main__":
    main()
