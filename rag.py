import os
from typing import List, Tuple
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline  # <-- added

# Optional OpenAI LLM
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    from langchain_openai import ChatOpenAI
else:
    ChatOpenAI = None

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "storage")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_docs")

class LocalEmbedder(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = HuggingFaceEmbeddings(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embedder.embed_query(text)

class RAGPipeline:
    def __init__(self, persist_directory: str = STORAGE_DIR):
        os.makedirs(persist_directory, exist_ok=True)
        self.embedder = LocalEmbedder()
        self.db = Chroma(
            collection_name="rag_docs",
            embedding_function=self.embedder,
            persist_directory=persist_directory
        )

        if USE_OPENAI:
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        else:
            # ✅ Free local model fallback (CPU-friendly)
            gen_pipeline = pipeline(
                "text2text-generation",
                model="google/flan-t5-small",  # small, free, works on CPU
                max_new_tokens=256,
                device=-1  # CPU
            )
            self.llm = HuggingFacePipeline(pipeline=gen_pipeline)

    def _build_prompt(self, question: str, context: str) -> str:
        return f"""You are a helpful tutor. Use ONLY the context to answer.
If the answer isn't in the context, say you don't know.

Question: {question}

Context:
{context}

Answer:"""

    def answer(self, question: str, top_k: int = 4) -> Tuple[str, List[str]]:
        docs = self.db.similarity_search(question, k=top_k)
        context = "\n\n".join([d.page_content for d in docs])
        sources = [d.metadata.get("source", "unknown") for d in docs]

        prompt = self._build_prompt(question, context)
        resp = self.llm.invoke(prompt)
        text = resp.content if hasattr(resp, "content") else str(resp)

        return text, list(dict.fromkeys(sources))

# Singleton pipeline
_PIPELINE = None

def get_pipeline() -> RAGPipeline:
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = RAGPipeline()
        if _PIPELINE.db._collection.count() == 0:
            ingest_sample_docs(_PIPELINE)
    return _PIPELINE

def ingest_sample_docs(pipeline: RAGPipeline):
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    for fname in os.listdir(DOCS_DIR):
        path = os.path.join(DOCS_DIR, fname)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        chunks = splitter.split_documents([Document(page_content=content, metadata={"source": fname})])
        texts = [c.page_content for c in chunks]
        metas = [c.metadata for c in chunks]
        pipeline.db.add_texts(texts=texts, metadatas=metas)
        pipeline.db.persist()
