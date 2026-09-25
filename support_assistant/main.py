from fastapi import FastAPI

from schemas import AskRequest, AskResponse
from graph import ask, is_mock_mode

app = FastAPI(title="Zepto Support Assistant")


@app.get("/health")
def health():
    return {"status": "ok", "mock_llm": is_mock_mode()}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest) -> AskResponse:
    return ask(request.query)
