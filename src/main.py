from openai import OpenAI
from exa_py import Exa
from dotenv import load_dotenv
import os
from fastapi import FastAPI
from models.classes import Chat


app = FastAPI()


load_dotenv()

exaKey = os.environ.get("EXA_KEY")


@app.get("/health")
def healthroute():
    return "Hello"


@app.get("/chat")
def initChat(chat: Chat):
