from __future__ import annotations

from typing import Dict, Any, Optional

import re
import time

import requests


def music_platform_resolver(
    name: str,
    artist: str,
    type: str,
    year: Optional[int] = None,
    country: str = "us",
    retries: int = 3,
    backoff_base: float = 0.5,
) -> Dict[str, Any]:
    """Resolve a music entity to a platform URL using the iTunes Search API.

    Returns a dict matching the schema in docs/music_link_tools_schema.md.

    If resolution fails, returns a structure with platform/url set to None.
    """

    if type not in {"album", "track"}:
        raise ValueError(f"Unsupported type: {type!r}")

    entity = "album" if type == "album" else "song"
    term = f"{name} {artist}".strip()
    params = {
        "term": term,
        "entity": entity,
        "country": country,
        "limit": 10,
    }

    url = "https://itunes.apple.com/search"

    def _request() -> Dict[str, Any]:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    data: Optional[Dict[str, Any]] = None
    for attempt in range(retries):
        try:
            data = _request()
            break
        except requests.RequestException:
            if attempt == retries - 1:
                return {
                    "platform": None,
                    "url": None,
                    "confidence": 0.0,
                    "raw_response": {"error": "network failure"},
                }
            time.sleep(backoff_base * (2**attempt))

    results = data.get("results", []) if data else []
    if not results:
        return {
            "platform": None,
            "url": None,
            "confidence": 0.0,
            "raw_response": data or {},
        }

    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", s or "").strip().lower()

    norm_name = norm(name)
    norm_artist = norm(artist)
    best = None
    best_score = -1.0

    for item in results:
        title_key = "collectionName" if type == "album" else "trackName"
        artist_key = "artistName"
        item_title = norm(item.get(title_key, ""))
        item_artist = norm(item.get(artist_key, ""))

        score = 0.0
        if item_title == norm_name:
            score += 0.6
        elif norm_name in item_title or item_title in norm_name:
            score += 0.3

        if norm_artist and norm_artist in item_artist:
            score += 0.3

        if year is not None:
            release_date = item.get("releaseDate")
            m = re.match(r"(\d{4})", release_date or "")
            if m:
                item_year = int(m.group(1))
                if item_year == year:
                    score += 0.2
                elif abs(item_year - year) <= 1:
                    score += 0.1

        if score > best_score:
            best_score = score
            best = item

    if not best:
        return {
            "platform": None,
            "url": None,
            "confidence": 0.0,
            "raw_response": data,
        }

    url_key = "collectionViewUrl" if type == "album" else "trackViewUrl"
    platform_url = best.get(url_key)
    if not platform_url:
        return {
            "platform": None,
            "url": None,
            "confidence": 0.0,
            "raw_response": data,
        }

    return {
        "platform": "apple_music",
        "url": platform_url,
        "confidence": min(1.0, max(0.0, best_score)),
        "raw_response": data,
    }


def smart_link_resolver(platform_url: str) -> Dict[str, Any]:
    """Convert a platform URL into a platform-agnostic smart link using song.link.

    Returns a dict with smartlink_url and redirector_url.
    """

    redirector_url = "https://song.link/" + platform_url

    try:
        resp = requests.get(redirector_url, allow_redirects=False, timeout=10)
    except requests.RequestException as e:
        return {
            "smartlink_url": None,
            "redirector_url": redirector_url,
            "error": f"network failure: {e}",
        }

    location = resp.headers.get("Location")
    if not location:
        return {
            "smartlink_url": None,
            "redirector_url": redirector_url,
            "error": "No Location header in redirect response",
        }

    return {
        "smartlink_url": location,
        "redirector_url": redirector_url,
    }
