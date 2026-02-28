"""
ai_engine/groq_client.py
========================
Groq API wrapper with rate limiting and retries.
Imported by test_generator.py.
Run standalone to test your API key.

HOW TO RUN (from project root):
    python ai_engine/groq_client.py

ALL SETTINGS ARE HARDCODED BELOW.
No config file, no CLI arguments, no relative imports.
"""

import time
import logging
from collections import deque
from typing import Optional
import os
from groq import Groq, RateLimitError, APIStatusError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
#  SETTINGS — edit these values directly
# =============================================================================

GROQ_API_KEY        = os.getenv("GROQ_API_KEY") 
GROQ_MODEL          = "llama-3.1-8b-instant"
GROQ_MAX_TOKENS     = 4096
GROQ_TEMPERATURE    = 0.3
REQUESTS_PER_MINUTE = 30     # free tier: 30 req/min
RETRY_ATTEMPTS      = 3
RETRY_DELAY_SEC     = 10     # seconds between retries

# =============================================================================


class _RateLimiter:
    def __init__(self):
        self.times = deque()

    def wait(self):
        now    = time.time()
        cutoff = now - 60
        while self.times and self.times[0] < cutoff:
            self.times.popleft()
        if len(self.times) >= REQUESTS_PER_MINUTE:
            wait = 61 - (now - self.times[0])
            if wait > 0:
                logger.info(f"  Rate limit — waiting {wait:.1f}s...")
                time.sleep(wait)
        self.times.append(time.time())


class GroqClient:
    def __init__(self):
        if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not set.\n"
                "Open ai_engine/groq_client.py and set GROQ_API_KEY = 'gsk_...'"
            )
        self.client  = Groq(api_key=GROQ_API_KEY)
        self.limiter = _RateLimiter()
        self.tokens  = 0
        self.calls   = 0

    def complete(self, system_prompt, user_prompt,
                 temperature=GROQ_TEMPERATURE,
                 max_tokens=GROQ_MAX_TOKENS,
                 expect_json=True) -> Optional[str]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        kwargs = dict(model=GROQ_MODEL, messages=messages,
                      temperature=temperature, max_tokens=max_tokens, stream=False)
        if expect_json:
            kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                self.limiter.wait()
                logger.info(f"  Groq call {attempt}/{RETRY_ATTEMPTS}...")
                resp = self.client.chat.completions.create(**kwargs)
                text = resp.choices[0].message.content
                self.tokens += resp.usage.total_tokens
                self.calls  += 1
                logger.info(f"  {resp.usage.total_tokens} tokens used (session total: {self.tokens})")
                return text
            except RateLimitError:
                wait = RETRY_DELAY_SEC * (2 ** (attempt - 1))
                logger.warning(f"  Rate limit hit — retrying in {wait}s...")
                time.sleep(wait)
            except APIStatusError as e:
                logger.error(f"  API error {e.status_code}: {e.message}")
                if attempt < RETRY_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SEC)
            except Exception as e:
                logger.error(f"  Error: {e}")
                if attempt < RETRY_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SEC)

        logger.error("  All retry attempts failed.")
        return None

    def usage(self):
        return {"calls": self.calls, "tokens": self.tokens}


if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"GROQ CONNECTION TEST  |  model={GROQ_MODEL}")
    print(f"{'='*55}\n")
    c = GroqClient()
    r = c.complete("You are a QA assistant.", "Reply with: Connection OK", expect_json=False)
    print(f"{'OK — ' + r if r else 'FAILED — check GROQ_API_KEY'}")
    print(f"Tokens used: {c.usage()['tokens']}")
    print(f"\nNext step: python ai_engine/test_generator.py")