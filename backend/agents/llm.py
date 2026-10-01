"""LLM client for NeerSetu agents — uses Groq (free) with llama-3.3-70b-versatile."""
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Best free Groq model: fast + capable enough for structured extraction
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_llm(model: str = GROQ_MODEL, temperature: float = 0.2) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY", "")
    return ChatGroq(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )
