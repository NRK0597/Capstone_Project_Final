import os
from typing import TypedDict

from pydantic import ValidationError

from ingest import build_index, retrieve_top_k
from prompt_template import build_policy_prompt
from schemas import AskResponse

POLICY_KEYWORDS = [
    "delivery", "return", "refund", "membership", "tracking", "cancel", "gift card", "support hours",
]

DIRECT_ANSWER_FALLBACK = "I can only answer questions about Zepto policies right now."


def is_mock_mode() -> bool:
    return os.environ.get("MOCK_LLM", "1") != "0"


class GraphState(TypedDict, total=False):
    query: str
    intent: str
    retrieved_chunks: list[dict]
    answer: str
    sources: list[str]
    confidence: float


# --------------------------------------------------------------------------- #
# Node 1:
# --------------------------------------------------------------------------- #
def classify_intent(state: GraphState) -> GraphState:
    query = state["query"]

    if is_mock_mode():
        lowered = query.lower()
        intent = "policy_question" if any(kw in lowered for kw in POLICY_KEYWORDS) else "general_question"
    else:
        intent = _llm_classify_intent(query)

    return {**state, "intent": intent}


def _llm_classify_intent(query: str) -> str:
    from llm_client import call_llm  # imported lazily; only needed in the optional path

    prompt = (
        "Classify the following customer query as exactly one word, either 'policy_question' (needs Zepto policy lookup) or 'general_question' "
        f"(does not). Query: {query!r}. Answer with one word only."
    )
    raw = call_llm(prompt)
    return "policy_question" if "policy" in raw.lower() else "general_question"


# --------------------------------------------------------------------------- #
# Node 2:
# --------------------------------------------------------------------------- #
def retrieve_and_answer(state: GraphState) -> GraphState:
    query = state["query"]

    build_index()
    chunks = retrieve_top_k(query, k=3)
    sources = [c["id"] for c in chunks]

    if is_mock_mode():
        top_chunk_snippet = chunks[0]["text"][:200] if chunks else ""
        answer = f"Based on the retrieved context: {top_chunk_snippet}"
        confidence = 1.0
    else:
        context = "\n\n".join(f"[{c['id']}] {c['text']}" for c in chunks)
        answer, confidence = _llm_generate_grounded_answer(query, context, sources)

    return {**state, "retrieved_chunks": chunks, "answer": answer,
            "sources": sources, "confidence": confidence}


def _llm_generate_grounded_answer(query: str, context: str, sources: list[str]) -> tuple[str, float]:
    from llm_client import call_llm_json

    prompt = build_policy_prompt(question=query, context=context)
    parsed = _call_with_schema_retry(prompt, call_llm_json, extra_sources=sources)
    return parsed.answer, parsed.confidence


# --------------------------------------------------------------------------- #
# Node 3:
# --------------------------------------------------------------------------- #
def direct_answer(state: GraphState) -> GraphState:
    query = state["query"]

    if is_mock_mode():
        answer = DIRECT_ANSWER_FALLBACK
        confidence = 1.0
    else:
        from llm_client import call_llm
        answer = call_llm(f"Answer this general question briefly: {query}")
        confidence = 0.8

    return {**state, "retrieved_chunks": [], "answer": answer, "sources": [], "confidence": confidence}


# --------------------------------------------------------------------------- #
# Schema validation retry logic for the optional real-LLM path
# --------------------------------------------------------------------------- #
def _call_with_schema_retry(prompt: str, llm_json_fn, extra_sources: list[str], max_retries: int = 2) -> AskResponse:
    last_error = None
    current_prompt = prompt
    for attempt in range(max_retries + 1):
        try:
            raw = llm_json_fn(current_prompt)
            candidate = dict(raw)
            candidate.setdefault("sources", extra_sources)
            return AskResponse(**candidate)
        except (ValidationError, ValueError, TypeError) as exc:
            last_error = exc
            current_prompt = (
                prompt
                + f"\n\nYour previous response was invalid ({exc}). "
                  "Return ONLY a valid JSON object matching the required schema."
            )
    return AskResponse(
        answer=f"[error] LLM output failed schema validation after {max_retries + 1} attempts: {last_error}",
        sources=extra_sources,
        confidence=0.0,
    )


# --------------------------------------------------------------------------- #
# Conditional routing.
# --------------------------------------------------------------------------- #
def route_after_classify(state: GraphState) -> str:
    return "retrieve_and_answer" if state["intent"] == "policy_question" else "direct_answer"


def build_graph():
    from langgraph.graph import StateGraph, START, END

    graph = StateGraph(GraphState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("retrieve_and_answer", retrieve_and_answer)
    graph.add_node("direct_answer", direct_answer)

    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {"retrieve_and_answer": "retrieve_and_answer", "direct_answer": "direct_answer"},
    )
    graph.add_edge("retrieve_and_answer", END)
    graph.add_edge("direct_answer", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def ask(query: str) -> AskResponse:
    result = get_graph().invoke({"query": query})
    return AskResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        confidence=result["confidence"],
    )


if __name__ == "__main__":
    for q in ["What is your delivery time?", "What is the capital of France?"]:
        print(f"\nQuery: {q!r}")
        print(ask(q).model_dump_json(indent=2))
