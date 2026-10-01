"""LLM client singleton for NeerSetu agents."""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


def get_llm(model: str = "gpt-4o", temperature: float = 0.2) -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "")
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )
