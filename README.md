# bandcamp-bulk-downloader

I needed a simple way to pull down entire discographies or individual albums from Bandcamp without clicking through every single page. This script takes an artist URL or album URL, finds all track streams (using the embedded player data), and downloads them in parallel into sorted directories.

It does not require API keys, just standard HTTP requests.

## Installation

Clone this repo and install dependencies:

```cmd
pip install -r requirements.txt
```

## How to run

To download an entire discography:
```cmd
python downloader.py https://some-artist.bandcamp.com
```

To download a specific album to a custom directory:
```cmd
python downloader.py https://some-artist.bandcamp.com/album/some-album -o D:\Music\Bandcamp
```

Limit download speed or download workers if you get rate limited:
```cmd
python downloader.py https://some-artist.bandcamp.com --workers 2
```

<!-- last-checked: 2026-09-22 -->
