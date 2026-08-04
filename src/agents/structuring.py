from config import STRUCTURING_MODEL, openai_client
from schemas import StructuredQuery

SYSTEM_PROMPT = """You extract structured creator-sourcing filters from a \
recruiter's natural-language brief. Only include platforms the user actually \
mentioned or clearly implied; if none are mentioned, include all three \
(tiktok, youtube, instagram). Leave numeric fields null if the brief doesn't \
specify them — do not invent numbers."""


async def structure_query(prompt: str) -> StructuredQuery:
    response = await openai_client.responses.parse(
        model=STRUCTURING_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        text_format=StructuredQuery,
    )
    return response.output_parsed
