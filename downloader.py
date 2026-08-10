import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import httpx

from bandcamp_bulk_downloader.parser import extract_tracks

# Lock to prevent terminal lines from overlapping during concurrent downloads
print_lock = Lock()

def safe_print(msg):
    with print_lock:
        print(msg)

def sanitize_filename(name):
    for char in '<>:"/\\|?*':
        name = name.replace(char, "_")
    return name.strip()

def download_track(client, track, output_dir):
    # FIXME: need a way to resume partial downloads without restarting the whole chunk stream
    album = track.get("album", "Unknown Album")
    title = track.get("title", "Unknown Track")
    url = track.get("stream_url")
    track_num = track.get("track_num", 0)

    if not url:
        safe_print(f"Skipping: {title} (no stream url available)")
        return

    # print(f"DEBUG: stream url for {title} is {url}")

    clean_album = sanitize_filename(album)
    clean_title = sanitize_filename(title)
    filename = f"{track_num:02d} - {clean_title}.mp3"
    
    album_dir = output_dir / clean_album
    album_dir.mkdir(parents=True, exist_ok=True)
    filepath = album_dir / filename

    safe_print(f"Downloading: {title}")
    
    try:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=16384):
                    f.write(chunk)
        safe_print(f"Finished: {title}")
    except httpx.HTTPStatusError as e:
        safe_print(f"Failed to download {title}: HTTP error {e.response.status_code}")
    except OSError as e:
        safe_print(f"Failed to write file {filename}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Download entire discographies or albums from Bandcamp",
        epilog="Example: python -m bandcamp_bulk_downloader.downloader https://artist.bandcamp.com"
    )
    parser.add_argument("url", help="Bandcamp artist or album URL")
    parser.add_argument("-o", "--output", default="downloads", help="Output directory path")
    parser.add_argument("-t", "--threads", type=int, default=4, help="Number of concurrent downloads")
    args = parser.parse_args()

    outputFolder = Path(args.output)

    try:
        tracks = extract_tracks(args.url)
    except httpx.RequestError as e:
        print(f"Network error while parsing page: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Parsing error: {e}", file=sys.stderr)
        sys.exit(1)

    if not tracks:
        print("No downloadable tracks found on the provided page.")
        return

    print(f"Found {len(tracks)} tracks. Starting concurrent download pool...")
    
    # We use a single shared client with connection pooling
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = [
                executor.submit(download_track, client, track, outputFolder)
                for track in tracks
            ]
            # Force wait for all threads to complete
            for fut in futures:
                try:
                    fut.result()
                except Exception as e:
                    # Catch unexpected errors in threads to prevent crash
                    print(f"Worker thread error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
