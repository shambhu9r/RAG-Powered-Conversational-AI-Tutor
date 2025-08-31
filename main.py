import os
from typing import Optional, List, Literal, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .rag import get_pipeline  # ✅ use your rag.py pipeline

load_dotenv()

app = FastAPI(title="Conversational RAG Tutor API")

# Enable CORS so frontend can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or ["http://localhost:3000"] to restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ Data Models ------------------
CHAT_HISTORY: Dict[str, List[Dict[str, str]]] = {}

Emotion = Literal["happy", "thinking", "explaining"]

class QueryRequest(BaseModel):
    question: str
    top_k: int = 4
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    text: str
    emotion: Emotion
    sources: List[str]

class ChatRequest(BaseModel):
    session_id: str
    message: str
    top_k: int = 4

class ChatResponse(BaseModel):
    text: str
    emotion: Emotion
    sources: List[str]
    session_id: str

# ------------------ Helpers ------------------
def infer_emotion(answer_text: str) -> Emotion:
    t = answer_text.lower()
    if any(k in t for k in ["let us think", "let's think", "step by step", "hmm", "consider"]):
        return "thinking"
    if any(k in t for k in ["great", "awesome", "nice job", "well done", "happy to"]):
        return "happy"
    return "explaining"

def run_rag(question: str, top_k: int = 4):
    pipeline = get_pipeline()
    answer, sources = pipeline.answer(question, top_k=top_k)
    return answer, sources

# ------------------ API Endpoints ------------------
@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    answer, sources = run_rag(req.question, top_k=req.top_k)
    emotion = infer_emotion(answer)
    if req.session_id:
        CHAT_HISTORY.setdefault(req.session_id, []).append({"role": "user", "content": req.question})
        CHAT_HISTORY[req.session_id].append({"role": "assistant", "content": answer})
    return QueryResponse(text=answer, emotion=emotion, sources=sources)

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = CHAT_HISTORY.setdefault(req.session_id, [])
    history.append({"role": "user", "content": req.message})

    # Build conversational context
    context_msgs = [f"{h['role'].upper()}: {h['content']}" for h in history[-10:]]
    prompt = "\n".join(context_msgs) + "\nASSISTANT:"

    # Run through RAG
    answer, sources = run_rag(prompt, top_k=req.top_k)

    history.append({"role": "assistant", "content": answer})
    emotion = infer_emotion(answer)

    return ChatResponse(text=answer, emotion=emotion, sources=sources, session_id=req.session_id)

@app.get("/health")
def health():
    return {"status": "ok"}
