import os
from dotenv import load_dotenv
from exa_py import AsyncExa
from openai import AsyncOpenAI

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
EXA_API_KEY = os.environ["EXA_API_KEY"]
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5000")

STRUCTURING_MODEL = os.environ.get("STRUCTURING_MODEL", "gpt-5.6-luna")
AGENT_MODEL = os.environ.get("AGENT_MODEL", "gpt-5.6-terra")
RANKING_MODEL = os.environ.get("RANKING_MODEL", "gpt-5.6-terra")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
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

MAX_SEARCH_ITERATIONS = 4
RESULTS_PER_SEARCH = 8

DEFAULT_FOLLOWER_MIN = 5_000
DEFAULT_MAX_RESULTS = 10
MIN_SHORTLIST_SCORE = 7

REFERENCE_RESULTS_PER_LOOKUP = 5

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
