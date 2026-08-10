import html
import json
import re
from urllib.parse import urljoin

# FIXME: some older albums have track_num as string or missing. Need to enforce integer conversion.

def extract_tralbum(html_content: str) -> dict:
    match = re.search(r'data-tralbum="([^"]+)"', html_content)
    if match:
        # print(f"DEBUG: Found data-tralbum, length={len(match.group(1))}")
        return json.loads(html.unescape(match.group(1)))
    
    # Fallback to inline TralbumData JS block (older themes use this)
    js_match = re.search(r'var\s+TralbumData\s*=\s*({.*?});', html_content, re.DOTALL)
    if js_match:
        js_text = js_match.group(1)
        try:
            return json.loads(js_text)
        except json.JSONDecodeError:
            # Quote unquoted JS object keys and strip trailing commas
            cleaned = re.sub(r'(\b\w+\b)\s*:', r'"\1":', js_text)
            cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
            
    raise ValueError("Could not find track or album data on this page. It might not be a valid Bandcamp page.")

def parse_album_page(html_content: str) -> dict:
    data = extract_tralbum(html_content)
    
    artist = data.get("artist") or ""
    if not artist and "current" in data:
        artist = data["current"].get("artist", "")
        
    album_title = data.get("current", {}).get("title") or ""
    
    tracks = []
    trackinfo = data.get("trackinfo", [])
    for track in trackinfo:
        file_info = track.get("file")
        stream_url = file_info.get("mp3-128") if file_info else None
        
        raw_num = track.get("track_num")
        try:
            track_num = int(raw_num) if raw_num is not None else None
        except ValueError:
            track_num = None

        tracks.append({
            "track_id": track.get("id") or track.get("track_id"),
            "title": track.get("title", "Unknown Track").strip(),
            "track_num": track_num,
            "stream_url": stream_url
        })
        
    return {
        "artist": artist.strip(),
        "album_title": album_title.strip(),
        "tracks": tracks
    }

def parse_artist_discography(html_content: str, base_url: str) -> list:
    links = re.findall(r'href="(/album/[^"]+|/track/[^"]+)"', html_content)
    seen = set()
    unique_links = []
    for link in links:
        clean_link = link.split("?")[0]
        full_url = urljoin(base_url, clean_link)
        if full_url not in seen:
            seen.add(full_url)
            unique_links.append(full_url)
    return unique_links
