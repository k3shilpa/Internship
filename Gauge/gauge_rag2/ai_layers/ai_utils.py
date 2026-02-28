# ai_layers/ai_utils.py - Groq API Client
# Groq is an OpenAI-compatible inference API (groq.com)
# Drop-in replacement for the original Ollama-based ai_utils.py

import json
import logging
import re
import time

from openai import OpenAI

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

# ── Singleton Groq client ─────────────────────────────────────────────────────
_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.GROK_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set!\n"
                "Run this in your terminal:\n"
                "  $env:GROQ_API_KEY='gsk_your-key-here'   (PowerShell)\n"
                "  export GROQ_API_KEY='gsk_your-key-here' (bash/mac)"
            )
        _client = OpenAI(
            api_key=config.GROK_API_KEY,
            base_url=config.GROK_BASE_URL,
            timeout=config.GROK_TIMEOUT,
        )
    return _client


# ── Core API call ─────────────────────────────────────────────────────────────

def call_ollama(prompt: str, system: str = "", json_mode: bool = False, retries: int = 3) -> str:
    """
    Main LLM call — kept as 'call_ollama' so all AI layers work without changes.
    Now routes to Groq API instead of local Ollama.
    """
    client = _get_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})

    # For JSON mode, append instruction directly in the prompt
    # (more reliable than response_format across all Groq models)
    if json_mode:
        messages.append({
            "role": "user",
            "content": prompt + "\n\nIMPORTANT: Respond with valid JSON only. No explanation, no markdown, no code fences. Just raw JSON."
        })
    else:
        messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model":       config.GROK_MODEL,
        "messages":    messages,
        "temperature": 0.2,
        "max_tokens":  4096,
    }

    for attempt in range(1, retries + 1):
        try:
            logger.debug(f"Groq request (attempt {attempt}/{retries}) model={config.GROK_MODEL}")
            response = client.chat.completions.create(**kwargs)
            result   = response.choices[0].message.content.strip()
            logger.debug(f"Groq response: {len(result)} chars")
            return result

        except Exception as e:
            logger.warning(f"Groq API error on attempt {attempt}/{retries}: {e}")
            if attempt == retries:
                raise
            wait = 2 ** attempt
            logger.info(f"Retrying in {wait}s...")
            time.sleep(wait)

    return ""


# ── JSON call ─────────────────────────────────────────────────────────────────

def call_ollama_json(prompt: str, system: str = "", retries: int = 3):
    """
    Call Groq and parse the response as a Python dict/list.
    Handles markdown code fences and partial JSON gracefully.
    """
    raw = call_ollama(prompt, system=system, json_mode=True, retries=retries)

    if not raw:
        logger.error("Groq returned an empty response.")
        return {}

    # Strip markdown code fences if model wraps output anyway
    if "```" in raw:
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if match:
            raw = match.group(1).strip()

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try to extract first JSON object or array from the string
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    logger.error(f"Could not parse JSON from Groq response:\n{raw[:500]}")
    return {}


# ── Embeddings ────────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list[float]:
    """
    Groq does not offer an embeddings endpoint.
    Uses OpenAI embeddings if configured, otherwise falls back to
    a deterministic hash-based pseudo-embedding (free, no API needed).
    """
    if config.EMBEDDING_PROVIDER == "openai" and config.OPENAI_API_KEY:
        try:
            from openai import OpenAI as OAI
            oai  = OAI(api_key=config.OPENAI_API_KEY)
            resp = oai.embeddings.create(input=text, model="text-embedding-3-small")
            return resp.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding failed, falling back to hash: {e}")

    return _hash_embedding(text)


def _hash_embedding(text: str, dims: int = 512) -> list[float]:
    """
    Deterministic pseudo-embedding using MD5 hashing.
    No API or GPU needed. Good enough for RAG retrieval in this project.
    """
    import hashlib, struct
    vector = []
    for i in range(dims):
        seed = f"{i}:{text}"
        h    = hashlib.md5(seed.encode()).digest()
        val  = struct.unpack("f", h[:4])[0]
        vector.append(val)
    # L2 normalise
    mag = sum(v * v for v in vector) ** 0.5
    return [v / mag for v in vector] if mag else vector


# ── Health check ──────────────────────────────────────────────────────────────

def check_ollama_health() -> bool:
    """
    Verify the Groq API key works and the configured model is reachable.
    Called 'check_ollama_health' to keep main_pipeline.py unchanged.
    """
    if not config.GROK_API_KEY:
        logger.error(
            "GROQ_API_KEY is not set!\n"
            "  PowerShell : $env:GROQ_API_KEY='gsk_your-key-here'\n"
            "  .env file  : GROQ_API_KEY=gsk_your-key-here"
        )
        return False

    try:
        client = _get_client()
        client.chat.completions.create(
            model=config.GROK_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        logger.info(f"✓ Groq API healthy. Model: {config.GROK_MODEL}")
        return True

    except Exception as e:
        logger.error(f"Groq API health check failed: {e}")
        return False
