"""Fetch setlist.fm data for top 50 Metal Archives bands by review count."""

import csv
import json
import os
import time
from collections import Counter
from pathlib import Path

import requests

_key_file = Path(".setlist/api_key")
API_KEY = os.environ.get("SETLISTFM_API_KEY") or (
    _key_file.read_text().strip() if _key_file.exists() else None
)
if not API_KEY:
    raise RuntimeError("Set SETLISTFM_API_KEY env var or create .setlist/api_key file")
BASE_URL = "https://api.setlist.fm/rest/1.0"
HEADERS = {"Accept": "application/json", "x-api-key": API_KEY}
RATE_LIMIT_DELAY = 0.6  # ~1.7 req/sec, safely under setlist.fm's 2/sec limit
MAX_RETRIES = 5

DATA_DIR = Path("data/raw/metal_archives")
OUT_DIR = Path("data/raw/setlistfm")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_top_bands(n: int = 50) -> list[dict]:
    """Return top N bands by total review count."""
    # Count reviews per band
    review_counts: Counter[str] = Counter()
    with open(DATA_DIR / "all_bands_discography.csv") as f:
        for row in csv.DictReader(f):
            r = row.get("Reviews", "")
            if r and r != "No Reviews":
                try:
                    count = int(r.split("(")[0].strip())
                    review_counts[row["Band ID"]] += count
                except ValueError:
                    pass

    top_ids = {bid for bid, _ in review_counts.most_common(n)}

    # Load band info for those IDs (deduplicate, keep first occurrence)
    bands = []
    seen = set()
    with open(DATA_DIR / "metal_bands.csv") as f:
        for row in csv.DictReader(f):
            bid = row["Band ID"]
            if bid in top_ids and bid not in seen:
                bands.append(row)
                seen.add(bid)
    return bands


def api_get(url: str, params: dict | None = None) -> requests.Response | None:
    """GET with rate limiting and retry on 429."""
    for attempt in range(MAX_RETRIES):
        time.sleep(RATE_LIMIT_DELAY)
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code == 429:
            wait = 5 * (attempt + 1)
            print(f"  Rate limited, waiting {wait}s (attempt {attempt+1}/{MAX_RETRIES})...")
            time.sleep(wait)
            continue
        return resp
    return resp  # return last response even if still 429


def search_artist(name: str) -> dict | None:
    """Search setlist.fm for an artist by name. Return first exact match."""
    resp = api_get(f"{BASE_URL}/search/artists", {"artistName": name, "sort": "relevance"})
    if resp is None or resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    for artist in data.get("artist", []):
        if artist.get("name", "").lower() == name.lower():
            return artist
    # Fall back to first result if no exact match
    artists = data.get("artist", [])
    return artists[0] if artists else None


def fetch_setlists(mbid: str, max_pages: int = 5) -> list[dict]:
    """Fetch setlists for an artist by MusicBrainz ID, up to max_pages."""
    all_setlists = []
    for page in range(1, max_pages + 1):
        resp = api_get(f"{BASE_URL}/artist/{mbid}/setlists", {"p": page})
        if resp is None or resp.status_code == 404:
            break
        resp.raise_for_status()
        data = resp.json()
        setlists = data.get("setlist", [])
        if not setlists:
            break
        all_setlists.extend(setlists)
        total = int(data.get("total", 0))
        items_per_page = int(data.get("itemsPerPage", 20))
        if page * items_per_page >= total:
            break
    return all_setlists


def flatten_setlist(setlist: dict) -> tuple[dict, list[dict]]:
    """Flatten a setlist JSON into a setlist record and song records."""
    venue = setlist.get("venue", {})
    city = venue.get("city", {})
    country = city.get("country", {})
    coords = city.get("coords", {})

    setlist_record = {
        "setlist_id": setlist.get("id", ""),
        "artist_mbid": setlist.get("artist", {}).get("mbid", ""),
        "artist_name": setlist.get("artist", {}).get("name", ""),
        "event_date": setlist.get("eventDate", ""),
        "venue_id": venue.get("id", ""),
        "venue_name": venue.get("name", ""),
        "city_name": city.get("name", ""),
        "state": city.get("state", ""),
        "country_code": country.get("code", ""),
        "country_name": country.get("name", ""),
        "latitude": coords.get("lat"),
        "longitude": coords.get("long"),
        "tour_name": setlist.get("tour", {}).get("name", "") if setlist.get("tour") else "",
    }

    songs = []
    for s in setlist.get("sets", {}).get("set", []):
        set_name = s.get("name", "")
        encore = s.get("encore", 0)
        for song in s.get("song", []):
            cover = song.get("cover", {})
            songs.append({
                "setlist_id": setlist.get("id", ""),
                "song_name": song.get("name", ""),
                "set_name": set_name,
                "encore": encore,
                "is_cover": bool(cover),
                "cover_artist_name": cover.get("name", "") if cover else "",
                "is_tape": song.get("tape", False),
            })

    return setlist_record, songs


SETLIST_FIELDS = [
    "setlist_id", "artist_mbid", "artist_name", "event_date", "venue_id",
    "venue_name", "city_name", "state", "country_code", "country_name",
    "latitude", "longitude", "tour_name",
]
SONG_FIELDS = [
    "setlist_id", "song_name", "set_name", "encore", "is_cover",
    "cover_artist_name", "is_tape",
]
MAPPING_FIELDS = [
    "ma_band_id", "ma_band_name", "sfm_mbid", "sfm_artist_name", "match_type",
]


def init_csv(path: Path, fieldnames: list[str]):
    """Write CSV header if file doesn't exist."""
    if not path.exists():
        with open(path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()


def append_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    """Append rows to an existing CSV."""
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writerows(rows)


def main():
    print("Loading top 50 bands by review count...")
    bands = get_top_bands(50)
    print(f"Found {len(bands)} bands to query")

    checkpoint_path = OUT_DIR / "checkpoint.json"
    processed = set()
    if checkpoint_path.exists():
        processed = set(json.loads(checkpoint_path.read_text()))
        print(f"Resuming — {len(processed)} bands already processed")

    setlists_path = OUT_DIR / "setlists.csv"
    songs_path = OUT_DIR / "songs.csv"
    mapping_path = OUT_DIR / "band_mapping.csv"
    init_csv(setlists_path, SETLIST_FIELDS)
    init_csv(songs_path, SONG_FIELDS)
    init_csv(mapping_path, MAPPING_FIELDS)

    total_setlists = 0
    total_songs = 0

    for i, band in enumerate(bands):
        band_id = band["Band ID"]
        band_name = band["Name"]

        if band_id in processed:
            continue

        print(f"[{i+1}/{len(bands)}] Searching: {band_name}...")
        artist = search_artist(band_name)

        if artist is None:
            print(f"  Not found on setlist.fm")
            processed.add(band_id)
            checkpoint_path.write_text(json.dumps(list(processed)))
            continue

        mbid = artist.get("mbid", "")
        match_type = "exact" if artist.get("name", "").lower() == band_name.lower() else "fuzzy"

        append_csv(mapping_path, [{
            "ma_band_id": band_id,
            "ma_band_name": band_name,
            "sfm_mbid": mbid,
            "sfm_artist_name": artist.get("name", ""),
            "match_type": match_type,
        }], MAPPING_FIELDS)

        print(f"  Matched: {artist.get('name', '')} (mbid={mbid}, {match_type})")
        print(f"  Fetching setlists...")

        setlists = fetch_setlists(mbid)
        print(f"  Got {len(setlists)} setlists")

        setlist_records = []
        song_records = []
        for sl in setlists:
            rec, songs = flatten_setlist(sl)
            setlist_records.append(rec)
            song_records.extend(songs)

        if setlist_records:
            append_csv(setlists_path, setlist_records, SETLIST_FIELDS)
        if song_records:
            append_csv(songs_path, song_records, SONG_FIELDS)

        total_setlists += len(setlist_records)
        total_songs += len(song_records)

        processed.add(band_id)
        checkpoint_path.write_text(json.dumps(list(processed)))

    print(f"\nDone! Total: {total_setlists} setlists, {total_songs} songs")


if __name__ == "__main__":
    main()
