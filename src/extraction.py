import re
from dataclasses import dataclass
from typing import Literal, Optional

UNIT_MULTIPLIERS = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}

MAX_PLAUSIBLE_FOLLOWERS = 500_000_000
TRIPLET_MAX_SPAN_CHARS = 240

LOW_RATIO_CEILING = 2.0
HIGH_RATIO_FLOOR = 200.0

StatConfidence = Literal["triplet", "pair", "weak", "none"]
EngagementBand = Literal["low", "healthy", "very_high", "unknown"]

_STAT_PATTERN = re.compile(
    r"([\d][\d,.]*)\s*([KMB])?\s*(Following|Followers|Likes)(?![A-Za-z])",
    re.IGNORECASE,
)

_CHROME_PATTERN = re.compile(
    r"suggested\s+accounts?"
    r"|accounts?\s+to\s+follow"
    r"|you\s+may\s+(?:also\s+)?like"
    r"|related\s+accounts?"
    r"|people\s+also"
    r"|discover\s+more",
    re.IGNORECASE,
)


@dataclass
class ProfileStats:
    followers: Optional[int] = None
    likes: Optional[int] = None
    following: Optional[int] = None
    confidence: StatConfidence = "none"


def parse_stat_number(digits: str, unit: Optional[str]) -> Optional[int]:
    cleaned = digits.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if unit:
        value *= UNIT_MULTIPLIERS[unit.upper()]
    if value < 0:
        return None
    return int(value)


def _collect_matches(text: str) -> list[tuple[str, Optional[int], int, int]]:
    collected = []
    for match in _STAT_PATTERN.finditer(text):
        value = parse_stat_number(match.group(1), match.group(2))
        if value is None:
            continue
        label = match.group(3).lower()
        collected.append((label, value, match.start(), match.end()))
    return collected


def strip_recommendation_chrome(text: str) -> str:
    match = _CHROME_PATTERN.search(text)
    if match:
        return text[: match.start()]
    return text


def extract_profile_stats(text: Optional[str]) -> ProfileStats:
    if not text:
        return ProfileStats()

    own_text = strip_recommendation_chrome(text)
    matches = _collect_matches(own_text)
    if not matches:
        return ProfileStats()

    for i in range(len(matches) - 2):
        first, second, third = matches[i], matches[i + 1], matches[i + 2]
        labels = (first[0], second[0], third[0])
        if labels != ("following", "followers", "likes"):
            continue
        if third[3] - first[2] > TRIPLET_MAX_SPAN_CHARS:
            continue
        if second[1] > MAX_PLAUSIBLE_FOLLOWERS:
            continue
        return ProfileStats(
            followers=second[1],
            likes=third[1],
            following=first[1],
            confidence="triplet",
        )

    for i in range(len(matches) - 1):
        current, following_match = matches[i], matches[i + 1]
        if (current[0], following_match[0]) != ("followers", "likes"):
            continue
        if following_match[3] - current[2] > TRIPLET_MAX_SPAN_CHARS:
            continue
        if current[1] > MAX_PLAUSIBLE_FOLLOWERS:
            continue
        return ProfileStats(
            followers=current[1],
            likes=following_match[1],
            confidence="pair",
        )

    for label, value, _, _ in matches:
        if label != "followers":
            continue
        if value > MAX_PLAUSIBLE_FOLLOWERS:
            continue
        return ProfileStats(followers=value, confidence="weak")

    return ProfileStats()


def likes_per_follower(
    likes: Optional[int], followers: Optional[int]
) -> Optional[float]:
    if not likes or not followers:
        return None
    return round(likes / followers, 2)


def engagement_band(ratio: Optional[float]) -> EngagementBand:
    if ratio is None:
        return "unknown"
    if ratio < LOW_RATIO_CEILING:
        return "low"
    if ratio >= HIGH_RATIO_FLOOR:
        return "very_high"
    return "healthy"
