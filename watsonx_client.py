"""
watsonx_client.py
-----------------
Thin wrapper around ibm-watsonx-ai for text generation.

• Uses the chat API (/ml/v1/text/chat) — the current recommended endpoint.
• Auto-detects the best available instruct model in your watsonx.ai region
  if the configured model is not supported (fallback chain).
• The active model ID is cached per process after the first successful init.
"""

import os
import logging
import warnings
from dotenv import load_dotenv

load_dotenv()

# Suppress the deprecation lifecycle warnings IBM emits — they're informational,
# not errors, and clutter the console.
warnings.filterwarnings("ignore", category=Warning, module="ibm_watsonx_ai")

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

logger = logging.getLogger(__name__)

# ── Fallback model preference order ──────────────────────────────────────────
# Tried in order; first one accepted by your project/region is used.
MODEL_FALLBACK_CHAIN = [
    # Granite instruct models (preferred — best for structured JSON output)
    "ibm/granite-3-3-8b-instruct",
    "ibm/granite-3-2-8b-instruct",
    "ibm/granite-3-1-8b-instruct",
    "ibm/granite-8b-code-instruct",      # deprecated but still works in au-syd
    "ibm/granite-13b-instruct-v2",
    "ibm/granite-13b-chat-v2",
    "ibm/granite-3-1-8b-base",
    # Llama instruct fallbacks
    "meta-llama/llama-3-3-70b-instruct",
    "meta-llama/llama-3-1-70b-instruct",
    "meta-llama/llama-3-1-8b-instruct",
    "meta-llama/llama-3-1-8b",
]

# ── Module-level cache ────────────────────────────────────────────────────────
_model_instance: ModelInference | None = None
_active_model_id: str | None = None


def _build_params() -> dict:
    return {
        GenParams.MAX_NEW_TOKENS:     int(os.getenv("MAX_NEW_TOKENS",      2048)),
        GenParams.MIN_NEW_TOKENS:     int(os.getenv("MIN_NEW_TOKENS",      50)),
        GenParams.TEMPERATURE:        float(os.getenv("TEMPERATURE",       0.7)),
        GenParams.TOP_P:              float(os.getenv("TOP_P",             0.9)),
        GenParams.TOP_K:              int(os.getenv("TOP_K",               50)),
        GenParams.REPETITION_PENALTY: float(os.getenv("REPETITION_PENALTY",1.1)),
    }


def _get_model() -> ModelInference:
    """
    Return a cached ModelInference instance, probing the fallback chain
    to find a model supported in the current watsonx.ai environment.
    """
    global _model_instance, _active_model_id

    if _model_instance is not None:
        return _model_instance

    api_key    = os.getenv("WATSONX_API_KEY", "").strip()
    project_id = os.getenv("WATSONX_PROJECT_ID", "").strip()
    url        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").strip()
    configured = os.getenv("GRANITE_MODEL_ID", "ibm/granite-8b-code-instruct").strip()

    if not api_key or not project_id:
        raise EnvironmentError(
            "WATSONX_API_KEY and WATSONX_PROJECT_ID must be set in your .env file."
        )

    credentials = Credentials(url=url, api_key=api_key)
    params = _build_params()

    probe_order = [configured] + [m for m in MODEL_FALLBACK_CHAIN if m != configured]

    last_error = None
    for model_id in probe_order:
        try:
            logger.info("Trying model: %s …", model_id)
            instance = ModelInference(
                model_id=model_id,
                credentials=credentials,
                project_id=project_id,
                params=params,
            )
            _model_instance = instance
            _active_model_id = model_id
            if model_id != configured:
                logger.warning(
                    "Configured model '%s' unavailable — using '%s' instead. "
                    "Update GRANITE_MODEL_ID in .env to silence this.",
                    configured, model_id,
                )
            else:
                logger.info("Model '%s' initialised.", model_id)
            return _model_instance
        except Exception as exc:
            logger.debug("Model '%s' unavailable: %s", model_id, exc)
            last_error = exc

    raise RuntimeError(
        f"No supported model found in your watsonx.ai environment.\n"
        f"Tried: {probe_order}\nLast error: {last_error}\n"
        f"Check your WATSONX_URL and project permissions."
    )


def get_active_model_id() -> str | None:
    """Return the model ID currently in use (None before first call)."""
    return _active_model_id


def generate(prompt: str) -> str:
    """
    Send a prompt via the chat API and return the assistant reply text.

    Uses chat() → /ml/v1/text/chat (current recommended endpoint).
    The response dict has the shape:
      {"choices": [{"message": {"content": "..."}}], ...}
    """
    try:
        model = _get_model()

        messages = [{"role": "user", "content": prompt}]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = model.chat(messages=messages)

        # Extract text from the chat response dict
        text = (
            response
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return text.strip() if text else ""

    except EnvironmentError:
        raise
    except Exception as exc:
        logger.error("Generation error: %s", exc, exc_info=True)
        raise RuntimeError(f"Model generation failed: {exc}") from exc
