import os
from dotenv import load_dotenv
from exa_py import AsyncExa
from openai import AsyncOpenAI

load_dotenv()

def env(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or default


OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
OPENROUTER_BASE_URL = env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
EXA_API_KEY = os.environ["EXA_API_KEY"]
FRONTEND_ORIGIN = env("FRONTEND_ORIGIN", "http://localhost:5000")

STRUCTURING_MODEL = env("STRUCTURING_MODEL", "openai/gpt-5.6-luna")
AGENT_MODEL = env("AGENT_MODEL", "openai/gpt-5.6-terra")
RANKING_MODEL = env("RANKING_MODEL", "openai/gpt-5.6-terra")
EMBEDDING_MODEL = env("EMBEDDING_MODEL", "openai/text-embedding-3-small")

openai_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    default_headers={
        "HTTP-Referer": "https://github.com/kol-research-tool",
        "X-Title": "KOL Creator Research Tool",
    },
)
exa_client = AsyncExa(api_key=EXA_API_KEY)

PLATFORM_DOMAINS = {
    "tiktok": ["tiktok.com"],
    "youtube": ["youtube.com"],
    "instagram": ["instagram.com"],
}

PLATFORM_QUERY_FRAME = {
    "tiktok": "TikTok profile page of a",
    "youtube": "YouTube channel homepage of a",
    "instagram": "Instagram profile page of a",
}

MAX_SEARCH_ITERATIONS = int(env("MAX_SEARCH_ITERATIONS", "5"))
RESULTS_PER_SEARCH = int(env("RESULTS_PER_SEARCH", "15"))

DEFAULT_FOLLOWER_MIN = int(env("DEFAULT_FOLLOWER_MIN", "2000"))
DEFAULT_MAX_RESULTS = int(env("DEFAULT_MAX_RESULTS", "15"))
MIN_SHORTLIST_SCORE = int(env("MIN_SHORTLIST_SCORE", "6"))

REFERENCE_RESULTS_PER_LOOKUP = 5

EXA_CACHE_TTL_SECONDS = int(env("EXA_CACHE_TTL_SECONDS", "3600"))
EXA_CACHE_MAX_ENTRIES = int(env("EXA_CACHE_MAX_ENTRIES", "500"))

YOUTUBE_API_KEY = env("YOUTUBE_API_KEY")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/channels"
YOUTUBE_BATCH_SIZE = 50

BIO_LINK_HOSTS = (
    "linktr.ee",
    "beacons.ai",
    "stan.store",
    "bio.link",
    "allmylinks.com",
    "komi.io",
    "taplink.cc",
    "snipfeed.co",
    "linkin.bio",
)
