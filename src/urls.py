import re
from dataclasses import dataclass
from typing import Literal, Optional
from urllib.parse import urlsplit

Platform = Literal["tiktok", "youtube", "instagram"]

PLATFORM_HOSTS = {
    "tiktok.com": "tiktok",
    "instagram.com": "instagram",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
}

NON_PROFILE_SEGMENTS = {
    "video",
    "p",
    "reel",
    "reels",
    "shorts",
    "watch",
    "explore",
    "discover",
    "tag",
    "search",
    "playlist",
    "hashtag",
    "music",
    "live",
}

YOUTUBE_PREFIX_SEGMENTS = {"c", "channel", "user"}

_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:tiktok\.com|instagram\.com|youtube\.com|youtu\.be)"
    r"/[^\s,;)\]\"'<>]+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProfileRef:
    platform: Platform
    handle: str
    canonical_url: str


def find_profile_urls(text: str) -> list[str]:
    if not text:
        return []
    seen: list[str] = []
    for raw in _URL_PATTERN.findall(text):
        cleaned = raw.rstrip(".,;:!?")
        if cleaned not in seen:
            seen.append(cleaned)
    return seen


def _host_platform(host: str) -> Optional[Platform]:
    host = host.lower().removeprefix("www.")
    return PLATFORM_HOSTS.get(host)


def _split_path(url: str) -> tuple[Optional[Platform], list[str]]:
    candidate = url if "://" in url else f"https://{url}"
    parts = urlsplit(candidate)
    platform = _host_platform(parts.netloc)
    if platform is None:
        return None, []
    segments = [s for s in parts.path.split("/") if s]
    return platform, segments


def canonical_profile_url(platform: Platform, handle: str) -> str:
    if platform == "tiktok":
        return f"https://www.tiktok.com/@{handle}"
    if platform == "instagram":
        return f"https://www.instagram.com/{handle}"
    if handle.startswith("UC") and len(handle) > 20:
        return f"https://www.youtube.com/channel/{handle}"
    return f"https://www.youtube.com/@{handle}"


def parse_profile_url(url: str) -> Optional[ProfileRef]:
    platform, segments = _split_path(url)
    if platform is None or not segments:
        return None

    first = segments[0]

    if platform == "youtube" and first.lower() in YOUTUBE_PREFIX_SEGMENTS:
        if len(segments) < 2:
            return None
        handle = segments[1]
    else:
        if first.lower() in NON_PROFILE_SEGMENTS:
            return None
        handle = first

    handle = handle.lstrip("@")
    if not handle:
        return None

    return ProfileRef(
        platform=platform,
        handle=handle,
        canonical_url=canonical_profile_url(platform, handle),
    )


def is_profile_url(url: str) -> bool:
    platform, segments = _split_path(url)
    if platform is None or not segments:
        return False
    if any(segment.lower() in NON_PROFILE_SEGMENTS for segment in segments):
        return False
    if platform == "youtube":
        return len(segments) <= 2
    return len(segments) == 1


def normalize_url(url: str) -> str:
    ref = parse_profile_url(url)
    if ref is not None and is_profile_url(url):
        return ref.canonical_url
    candidate = url if "://" in url else f"https://{url}"
    parts = urlsplit(candidate)
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    return f"https://{host}{path}"


def dedupe_key(platform: str, handle: str) -> str:
    return f"{platform}|{handle.lstrip('@').lower()}"
