from typing import Literal, Optional

from pydantic import BaseModel

from config import DEFAULT_FOLLOWER_MIN, DEFAULT_MAX_RESULTS, STRUCTURING_MODEL, openai_client
from cost import CostTracker
from schemas import Platform, ReferenceAccount, StructuredQuery
from urls import find_profile_urls, parse_profile_url

SYSTEM_PROMPT = """You extract structured creator-sourcing filters from a \
recruiter's natural-language brief.

Rules:
- Only include platforms the user mentioned or clearly implied. If the brief \
names none, include all three (tiktok, youtube, instagram).
- Reference accounts have already been extracted for you and are listed \
separately. Never copy their URLs or handles into niche_keywords.
- niche_keywords describe the subject matter (e.g. "options trading", \
"personal finance"), not the platform or follower counts.
- exclude_keywords capture what the user does NOT want (e.g. "big established \
names" implies excluding mainstream celebrity accounts).
- Leave numeric fields null when the brief does not state them. Never invent \
numbers.
- audience_geo is where the AUDIENCE is, not the creator."""


class _QueryDraft(BaseModel):
    platforms: list[Platform]
    niche_keywords: list[str]
    audience_age_min: Optional[int] = None
    audience_age_max: Optional[int] = None
    audience_gender_skew: Optional[str] = None
    audience_geo: Optional[str] = None
    follower_min: Optional[int] = None
    follower_max: Optional[int] = None
    exclude_keywords: list[str] = []
    max_results: Optional[int] = None
    other_notes: Optional[str] = None


def extract_reference_accounts(prompt: str) -> list[ReferenceAccount]:
    accounts: list[ReferenceAccount] = []
    seen: set[str] = set()
    for url in find_profile_urls(prompt):
        ref = parse_profile_url(url)
        if ref is None:
            continue
        key = f"{ref.platform}|{ref.handle.lower()}"
        if key in seen:
            continue
        seen.add(key)
        accounts.append(
            ReferenceAccount(
                platform=ref.platform, handle=ref.handle, url=ref.canonical_url
            )
        )
    return accounts


def _describe_references(accounts: list[ReferenceAccount]) -> str:
    if not accounts:
        return "Reference accounts: none."
    listed = ", ".join(f"{a.handle} ({a.platform})" for a in accounts)
    return f"Reference accounts already extracted: {listed}."


def apply_defaults(query: StructuredQuery) -> StructuredQuery:
    updates: dict = {}
    if query.follower_min is None:
        updates["follower_min"] = DEFAULT_FOLLOWER_MIN
    if query.max_results is None:
        updates["max_results"] = DEFAULT_MAX_RESULTS
    if not query.platforms:
        updates["platforms"] = ["tiktok", "youtube", "instagram"]
    if not updates:
        return query
    return query.model_copy(update=updates)


async def structure_query(
    prompt: str, tracker: Optional[CostTracker] = None
) -> StructuredQuery:
    references = extract_reference_accounts(prompt)

    response = await openai_client.chat.completions.parse(
        model=STRUCTURING_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{_describe_references(references)}\n\nBrief: {prompt}",
            },
        ],
        response_format=_QueryDraft,
    )
    if tracker:
        tracker.record_response(STRUCTURING_MODEL, response)

    draft = response.choices[0].message.parsed
    query = StructuredQuery(
        **draft.model_dump(), reference_accounts=references
    )
    return apply_defaults(query)
