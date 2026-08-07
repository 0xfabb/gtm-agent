import asyncio
import re
from typing import Awaitable, Callable, Optional

import exa_cache
from config import BIO_LINK_HOSTS, REFERENCE_RESULTS_PER_LOOKUP, STRUCTURING_MODEL, openai_client
from cost import CostTracker
from schemas import ReferenceAccount, SeedProfile

EmitFn = Callable[[dict], Awaitable[None]]

SYSTEM_PROMPT = """You are profiling reference creators so a search system can \
find others like them.

You will receive raw web search text about one or more reference accounts. \
Write a seed profile describing what these creators actually make.

Rules:
- Base everything on the supplied text. If it is thin, say so in the summary \
and keep the profile general rather than inventing specifics.
- search_descriptions must be 3-5 natural-language descriptions of the KIND of \
creator to look for, written as content descriptions, not as names or handles. \
Good: "TikTok creator explaining options flow and implied volatility to retail \
traders". Bad: "creators like @valatility".
- Never include the reference handles or URLs in search_descriptions."""

_BIO_LINK_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:" + "|".join(re.escape(h) for h in BIO_LINK_HOSTS) + r")/[^\s,;)\]\"'<>]+",
    re.IGNORECASE,
)


def find_bio_links(text: Optional[str]) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for match in _BIO_LINK_PATTERN.findall(text):
        cleaned = match.rstrip(".,;:!?")
        if cleaned not in found:
            found.append(cleaned)
    return found


async def _lookup_reference(reference: ReferenceAccount, emit: EmitFn) -> str:
    query = f"{reference.handle} {reference.platform} creator profile"
    await emit(
        {
            "type": "agent_step",
            "agent": "references",
            "action": "searching",
            "query": query,
        }
    )

    response = await exa_cache.search(
        query,
        num_results=REFERENCE_RESULTS_PER_LOOKUP,
        contents={"text": {"maxCharacters": 1200}},
    )

    chunks: list[str] = []
    bio_links: list[str] = []
    for result in response.results:
        chunks.append(f"[{result.url}] {result.title or ''} {result.text or ''}")
        bio_links.extend(find_bio_links(result.text))
        bio_links.extend(find_bio_links(result.url))
        await emit(
            {
                "type": "agent_step",
                "agent": "references",
                "action": "found",
                "result": {"url": result.url, "title": result.title},
            }
        )

    for link in bio_links[:2]:
        try:
            await emit(
                {
                    "type": "agent_step",
                    "agent": "references",
                    "action": "searching",
                    "query": f"bio link: {link}",
                }
            )
            contents = await exa_cache.get_contents(
                [link], text={"maxCharacters": 1200}
            )
            for result in contents.results:
                chunks.append(f"[bio-link {result.url}] {result.text or ''}")
        except Exception:
            continue

    return "\n\n".join(chunks)


async def resolve_references(
    references: list[ReferenceAccount],
    emit: EmitFn,
    tracker: Optional[CostTracker] = None,
) -> Optional[SeedProfile]:
    if not references:
        return None

    try:
        gathered = await asyncio.gather(
            *(_lookup_reference(reference, emit) for reference in references)
        )
    except Exception as exc:
        await emit({"type": "error", "agent": "references", "message": str(exc)})
        return None

    evidence = "\n\n".join(chunk for chunk in gathered if chunk).strip()
    if not evidence:
        await emit(
            {
                "type": "error",
                "agent": "references",
                "message": "No web evidence found for the reference accounts.",
            }
        )
        return None

    listed = ", ".join(f"@{r.handle} ({r.platform})" for r in references)

    try:
        response = await openai_client.responses.parse(
            model=STRUCTURING_MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Reference accounts: {listed}\n\nWeb evidence:\n{evidence}",
                },
            ],
            text_format=SeedProfile,
        )
    except Exception as exc:
        await emit({"type": "error", "agent": "references", "message": str(exc)})
        return None

    if tracker:
        tracker.record_response(STRUCTURING_MODEL, response)

    return response.output_parsed
