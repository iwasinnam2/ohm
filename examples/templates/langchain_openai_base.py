"""LangChain ChatOpenAI pointed at Ohm (OpenAI-compatible).

Prefer LOCAL until https://api.withohm.dev/v1 answers chat (docs/PLATFORM.md).
"""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

OHM_BASE = os.getenv("OHM_BASE_URL", "http://127.0.0.1:8081/v1")
OHM_KEY = os.getenv("OHM_API_KEY", "sk-at-dev")


def ohm_chat(model: str = "gpt-4o-mini") -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=OHM_KEY,
        base_url=OHM_BASE,
        temperature=0,
    )


if __name__ == "__main__":
    llm = ohm_chat(model="mock")
    print(llm.invoke("Say hi in one word").content)
