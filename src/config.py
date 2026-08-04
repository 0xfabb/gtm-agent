import os

from dotenv import load_dotenv
from exa_py import AsyncExa
from openai import AsyncOpenAI

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
EXA_API_KEY = os.environ["EXA_API_KEY"]
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

STRUCTURING_MODEL = "gpt-5.6-luna"
AGENT_MODEL = "gpt-5.6-luna"
RANKING_MODEL = "gpt-5.6-terra"

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
exa_client = AsyncExa(api_key=EXA_API_KEY)

PLATFORM_DOMAINS = {
    "tiktok": ["tiktok.com"],
    "youtube": ["youtube.com"],
    "instagram": ["instagram.com"],
}

MAX_SEARCH_ITERATIONS = 4
RESULTS_PER_SEARCH = 8
