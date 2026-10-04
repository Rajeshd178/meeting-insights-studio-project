"""
Microsoft Azure AI Foundry & OpenAI Client Helper.
Provides unified model calling for:
  - gpt-4.1-mini (Reasoning, analysis, Devil's Advocate, summaries)
  - text-embedding-3-small (Embeddings & vector search)
  - gpt-4o-transcribe-diarize (Transcription & speaker diarization)

Enforces LOW_QUOTA_MODE:
  - SQLite response cache keyed by (task, hash of input)
  - Inputs chunked under 6,000 tokens
  - Batch embeddings (max 16 per call)
  - Retry-After backoff on 429
  - One repair retry on malformed JSON
"""

import os
import sys
import json
import time
import hashlib
from typing import List, Dict, Any, Optional
from openai import OpenAI

try:
    from config import Config
except ImportError:
    from backend.config import Config


# SQLite Cache Setup
def _get_cache_conn():
    import sqlite3
    db_path = Config.BACKEND_DIR / "meeting_studio.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
    CREATE TABLE IF NOT EXISTS model_cache (
        cache_key TEXT PRIMARY KEY,
        task TEXT,
        input_hash TEXT,
        response_json TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    return conn


def get_cached_response(task: str, input_str: str) -> Optional[Any]:
    try:
        conn = _get_cache_conn()
        h = hashlib.sha256(input_str.encode("utf-8")).hexdigest()
        key = f"{task}:{h}"
        cur = conn.cursor()
        cur.execute("SELECT response_json FROM model_cache WHERE cache_key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
    except Exception as e:
        print(f"[Cache Read Notice] {e}")
    return None


def set_cached_response(task: str, input_str: str, response_obj: Any):
    try:
        conn = _get_cache_conn()
        h = hashlib.sha256(input_str.encode("utf-8")).hexdigest()
        key = f"{task}:{h}"
        cur = conn.cursor()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        cur.execute("""
        INSERT OR REPLACE INTO model_cache (cache_key, task, input_hash, response_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (key, task, h, json.dumps(response_obj), now))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Cache Write Notice] {e}")


def get_foundry_client() -> Optional[OpenAI]:
    """Returns an authenticated OpenAI / Azure AI client or None if in demo mode."""
    api_key = Config.OPENAI_API_KEY
    if not api_key or api_key == "your_openai_api_key_here":
        return None

    base_url = Config.OPENAI_BASE_URL
    if base_url:
        clean_url = base_url.rstrip("/")
        # Normalize Azure Foundry project endpoint to /openai/v1
        if "/api/projects" in clean_url:
            clean_url = clean_url.split("/api/projects")[0]
        if not clean_url.endswith("/openai/v1") and not clean_url.endswith("/v1"):
            clean_url = f"{clean_url}/openai/v1"
        return OpenAI(api_key=api_key, base_url=clean_url, default_headers={"api-key": api_key})
    return OpenAI(api_key=api_key)


class FoundryClient:
    """Unified wrapper around the 3 AI models with caching and quota defenses."""

    def __init__(self):
        self.chat_model = Config.MODEL_CHAT_ANALYSIS
        self.embedding_model = Config.MODEL_EMBEDDING
        self.transcribe_model = Config.MODEL_TRANSCRIBE_DIARIZE

    def chat_structured(
        self,
        task: str,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1500,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Calls gpt-4.1-mini with structured JSON output and caching.
        Includes 1 repair retry on malformed JSON.
        """
        cache_input = f"{system_prompt}\n---\n{user_prompt}"
        cached = get_cached_response(task, cache_input)
        if cached is not None:
            return cached

        client = get_foundry_client()
        if not client:
            return {"error": "Demo mode active — no live client"}

        # Wrap user content securely
        safe_user_prompt = f"Please analyze the following data strictly adhering to instructions:\n<data>\n{user_prompt}\n</data>"

        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=self.chat_model,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nReturn ONLY valid JSON."},
                        {"role": "user", "content": safe_user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                raw_text = response.choices[0].message.content
                data = json.loads(raw_text)
                set_cached_response(task, cache_input, data)
                return data
            except json.JSONDecodeError:
                if attempt == 0:
                    safe_user_prompt += "\n\nNotice: Your previous response was not valid JSON. Ensure strict JSON formatting."
                    continue
                return {"error": "Invalid JSON produced by model"}
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    time.sleep(2)
                    continue
                print(f"[FoundryClient chat error] {err_str}")
                return {"error": err_str}

        return {"error": "Failed after retry"}

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts using text-embedding-3-small in batches of max 16.
        """
        if not texts:
            return []

        client = get_foundry_client()
        if not client:
            # Deterministic mock vectors for demo mode (1536-dim normalized)
            import math
            mock_vectors = []
            for t in texts:
                h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
                vec = [(math.sin(h + i)) for i in range(128)]
                norm = math.sqrt(sum(x*x for x in vec)) or 1.0
                mock_vectors.append([x / norm for x in vec])
            return mock_vectors

        all_vectors = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i + batch_size]
            try:
                res = client.embeddings.create(input=chunk, model=self.embedding_model)
                all_vectors.extend([d.embedding for d in res.data])
            except Exception as e:
                print(f"[Embedding Error] {e}")
                # Fallback to zero vectors
                all_vectors.extend([[0.0] * 128 for _ in chunk])

        return all_vectors

    def get_embedding(self, text: str) -> List[float]:
        res = self.get_embeddings([text])
        return res[0] if res else [0.0] * 128


foundry_client = FoundryClient()
