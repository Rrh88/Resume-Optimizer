import os
import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

MODELS = list(dict.fromkeys(
    m for m in [
        os.getenv("GEMINI_MODEL"),
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
    ] if m
))


def get_llm(temperature: float = 0.2, model: str = None):
    return ChatGoogleGenerativeAI(
        model=model or MODELS[0],
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=temperature,
        max_retries=2,
        timeout=90,
    )


def invoke_structured(schema, prompt, temperature: float = 0.2):
    last = None
    for _ in range(3):
        for m in MODELS:
            try:
                return get_llm(temperature, m).with_structured_output(schema).invoke(prompt)
            except Exception as e:
                last = e
                time.sleep(2)
    raise last