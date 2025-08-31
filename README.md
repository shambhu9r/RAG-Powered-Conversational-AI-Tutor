# RAG Tutor Mascot (End-to-End)

A minimal, working scaffold for a conversational AI tutor with:
- **RAG backend** (FastAPI + LangChain + Chroma + Sentence-Transformers)
- **Live API** (`/query`, `/chat`)
- **Mascot UI** (React + Web Speech API for STT, Web Speech Synthesis for TTS)
- Emotion field: `"happy" | "thinking" | "explaining"`

## Quickstart

### Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt

# Optional: enable OpenAI LLM
export OPENAI_API_KEY=sk-...

# (One-time) ingest included sample docs
python ingest.py

# Run API
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm i
npm run dev
# open http://localhost:5173
```

Set `VITE_API_BASE` in a `.env` or shell when running the dev server if your API isn't at `http://localhost:8000`.

### Flow
1. Click **🎤 Speak** to use browser STT (Chromium/Edge).
2. Send with **/query** for single Q&A or **/chat** for multi-turn.
3. Mascot **speaks** the answer and changes **emotion** from the API.

### Notes
- Without `OPENAI_API_KEY`, the backend returns a context snippet (no generative LLM). Add the key for real answers.
- The vector store persists under `backend/storage`. Add your PDFs/MD/TXT into `backend/sample_docs/` and run `python backend/ingest.py`.
