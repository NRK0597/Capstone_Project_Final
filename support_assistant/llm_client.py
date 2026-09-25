import json
import os

_GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")


def _get_client():
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MOCK_LLM=0 requires GROQ_API_KEY to be set (if needed get a free key at console.groq.com). Leave MOCK_LLM unset/1 to use the required, fully offline mock path instead."
        )
    return Groq(api_key=api_key)


def call_llm(prompt: str) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=_GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content


def call_llm_json(prompt: str) -> dict:
    raw = call_llm(prompt)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)
