from typing import Dict, Any, List, Optional
import os
import yt_dlp

REQUEST_TIMEOUT = int(os.getenv('REQUESTS_TIMEOUT', '25'))

YDL_OPTS_BASE = {
    "quiet": True,
    "skip_download": True,   # Default: only extract metadata
    "nocheckcertificate": True,
    "geo_bypass": True,
    "socket_timeout": REQUEST_TIMEOUT,
    "http_headers": {
        # Helps when some CDNs require a UA
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    },
}


def extract_info(url: str, download: bool = False) -> Dict[str, Any]:
    """
    Extract metadata (and optionally download) for a given video URL.
    """
    opts = YDL_OPTS_BASE.copy()
    if not download:
        opts["skip_download"] = True
    else:
        opts["skip_download"] = False

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=download)
        return info


def pick_best_formats(info: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Pick the best MP4 format, a fallback, and the best thumbnail.
    """
    formats: List[Dict[str, Any]] = info.get("formats", [])

    def is_mp4(f: Dict[str, Any]) -> bool:
        ext = f.get("ext")
        vcodec = f.get("vcodec")
        return ext == "mp4" and (vcodec and vcodec != "none")

    mp4s = [f for f in formats if is_mp4(f) and f.get("url")]

    # Sort by resolution + bitrate
    mp4s.sort(key=lambda f: (f.get("height") or 0,
              f.get("tbr") or 0), reverse=True)

    best = mp4s[0] if mp4s else None
    fallback = mp4s[-1] if len(mp4s) > 1 else None

    # Pick largest thumbnail
    thumbnails = info.get("thumbnails") or []
    thumb = None
    if thumbnails:
        thumb = sorted(
            thumbnails, key=lambda t: (
                t.get("height") or 0, t.get("width") or 0)
        )[-1]

    return {"best": best, "fallback": fallback, "thumbnail": thumb}