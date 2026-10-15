"""Lightweight LLM client with persistent disk caching and token call logging."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class LLMClient:
    """Thin Gemini API wrapper with disk cache and audit token logging."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.0,
        cache_dir: str = "outputs/cache",
        log_file: str = "outputs/llm_calls.jsonl",
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def _get_cache_key(self, prompt: str) -> str:
        """Compute SHA-256 hash for model and prompt."""
        content = f"{self.model_name}:{self.temperature}:{prompt}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _log_call(
        self,
        prompt_hash: str,
        input_tokens: int,
        output_tokens: int,
        cached: bool,
    ) -> None:
        """Append LLM call metadata to jsonl log file."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model_name,
            "temperature": self.temperature,
            "prompt_hash": prompt_hash,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached": cached,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def generate_json(self, prompt: str, schema_description: str = "") -> Dict[str, Any]:
        """Generate structured JSON response, using disk cache if available."""
        prompt_hash = self._get_cache_key(prompt)
        cache_file = self.cache_dir / f"{prompt_hash}.json"

        # Check disk cache
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                self._log_call(
                    prompt_hash=prompt_hash,
                    input_tokens=0,
                    output_tokens=0,
                    cached=True,
                )
                return cached_data
            except Exception:
                pass  # Corrupted cache fallback

        # If no API key is set, raise RuntimeError
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment or .env file.")

        # Call Gemini API via google-genai SDK
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        full_prompt = (
            f"{prompt}\n\n"
            f"Output must be valid JSON only without markdown fences or code blocks. "
            f"{schema_description}"
        )

        response = client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                response_mime_type="application/json",
            ),
        )

        raw_text = response.text.strip()
        # Clean potential markdown wrapping if returned
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        parsed = json.loads(raw_text)

        # Estimate or extract usage metadata
        input_tokens = 0
        output_tokens = 0
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0
        else:
            input_tokens = len(full_prompt.split()) * 2
            output_tokens = len(raw_text.split()) * 2

        # Save to disk cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)

        # Log call
        self._log_call(
            prompt_hash=prompt_hash,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached=False,
        )

        return parsed
