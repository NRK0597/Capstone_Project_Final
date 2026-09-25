# Module 3-Support Assistant

## What I did in this module

I built a small chatbot style helper for Zepto that answers customer questions using Zepto's own policy documents. This is called a RAG system (Retrieval Augmented Generation), instead of the AI just making up an answer, it first looks up the most relevant policy text, and then builds its answer from that text.

The pieces I put together are:

- 8 policy documents (delivery, returns, membership, tracking, and so on) turned into number form (embeddings) and stored in a small local database called ChromaDB.
- A flow built with LangGraph that first checks if a question is about Zepto's policies or something else, and then sends it down the right path. A rule that the final answer always comes back in a fixed, checkable format (answer, sources, confidence) using Pydantic.
- A small web API built with FastAPI, with one endpoint POST /ask. A Dockerfile so the whole thing can be built and run inside a container.

## What was expected

- Take the 8 given policy documents, break them into pieces, turn them into embeddings using the all-MiniLM-L6-v2 model, and store them in ChromaDB.
- Write a proper prompt template with a role, context, task, format, and length, plus at least one rule about what NOT to do, and one example question answer pair.
- Build a LangGraph flow with at least 3 steps (nodes), one to figure out what kind of question it is, one to look up the answer using the documents, and one to answer general questions directly.
- Make sure that when MOCK_LLM is onby default, no step ever calls a real AI model as everything should work using fixed rules only. Always return the answer in a fixed structure, the answer text, which document(s) it came from, and a confidence number.
- Wrap all of this in a small API with FastAPI, and show at least 2 example questions and their answers. Write a Dockerfile so the app can also run inside a Docker container.

## What I got in the end

- All 8 documents are stored and can be searched using ChromaDB. The prompt template has all 5 required parts, plus a "do not" rule and an example, all written out as real text.
- The LangGraph flow has exactly 3 steps (classify_intent, retrieve_and_answer, direct_answer) and correctly sends questions down the right path. I tested this with both a policy question and a random question, and both went the correct way.
- When I search for something like "delivery", the system correctly pulls up the delivery policy document as the top result, so the search really is finding the right document, not just something random.
- The API works locally and inside Docker, and gives back the same correct answers both ways. I tested this myself by building and running the Docker container. The answer always comes back in the same structure (answer, sources, confidence), and this is checked automatically using Pydantic.

## How to set it up and run it

```bash
python -m venv .venv
.venv\Scripts\activate    
pip install -r support_assistant/requirements.txt
```

To run it on your own computer:

```bash
cd support_assistant
python ingest.py             
uvicorn main:app --host 0.0.0.0 --port 7860
```

To run it inside Docker instead:

```bash
cd support_assistant
docker build -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```

The mock setting (MOCK_LLM=1) is turned on by default inside the container too, so it runs the same way, fully offline.

## Problems I faced while building this and how I fixed them

When I tried to build and test the Docker part, my laptop said it didn't recognize the docker command at all. I had to install Docker Desktop from scratch, which also needed a Windows feature called WSL2 to be turned on. After installing it, I also had to restart my terminal because it kept saying docker was not found even after installing it.

The task is clear that even when MOCK_LLM is on, looking up the documents (the retrieval step) must still really happen, only the final AI-writing step should be skipped/faked. It would have been easy to accidentally skip the whole thing when mocking. I fixed this by writing the code so the document search always happens first, no matter what, and only the last part  checks whether mock mode is on or off.

## Example calls (recorded with MOCK_LLM=1)

1. The first question i asked is a policy question:

```
"What is your delivery time?"
```

```json
{
  "answer": "Based on the retrieved context: Delivery Policy: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order vol",
  "sources": ["doc_01", "doc_02", "doc_08"],
  "confidence": 1.0
}
```

2. A general question not related to this project

```
"What is the capital of France?"
```

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

I have tried a third example for checking a different keyword.

```
"Can I cancel my order?"
```

```json
{
  "answer": "Based on the retrieved context: Order Cancellation Policy: Orders can be cancelled free of cost any time before the order status changes to 'Packed', typically within the first 2 minutes of placing the order. Once an order has been ",
  "sources": ["doc_05", "doc_06", "doc_02"],
  "confidence": 1.0
}
```

In simple words:

- Getting the documents ready and turning them into numbers: done in ingest.py. And the numbers are stored in the ChromaDB collection named zepto_policies, set up to use cosine similarity.
- The retrieve_and_answer step inside graph.py and this step always really searches, in both mock mode and real mode. Also inside graph.py, either in retrieve_and_answer (for policy questions) or direct_answer (for general questions) is there. only the very last part of writing the answer checks whether MOCK_LLM is on or off. Everything before that like reading the documents, turning them into numbers, searching ChromaDB, and deciding which path to take is always happens the same way no matter what.
- The question type is decided using simple keyword matching, the policy answer is built from a fixed sentence template using the top search result, and the general answer is always the same fixed sentence.

## Files in this folder

```
support_assistant/
├── docs/doc_01.txt ... doc_08.txt   # the 8 policy documents, exactly as given
├── ingest.py                        # reads documents, makes embeddings, builds/searches ChromaDB
├── prompt_template.py               # the structured prompt (role/context/task/format/length + rule + example)
├── graph.py                         # the LangGraph flow
├── llm_client.py                
├── schemas.py                       # for the fixed answer format.
├── main.py                          # the FastAPI app with the POST /ask endpoint
├── Dockerfile
├── requirements.txt
└── chroma_db/                       # the search database.
```
