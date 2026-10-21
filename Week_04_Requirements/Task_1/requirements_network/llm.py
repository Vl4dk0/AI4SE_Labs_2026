"""OpenAI clients for the three allowed model ids.

The key is read from ASSIGNMENT_API_KEY and handed to ChatOpenAI directly.
It is never logged. A rejected model id stops the run instead of falling
through to some other model.
"""

from __future__ import annotations

import os
import re
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel, SecretStr, ValidationError

from .models import MODELS

_RETRYABLE = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
    OutputParserException,
    ValidationError,
    TimeoutError,
)

_CLIENTS: dict[str, ChatOpenAI] = {}
_LOCK = threading.Lock()
_KEY_RE = re.compile(r"sk-[A-Za-z0-9_-]+")


class ModelRejected(RuntimeError):
    """The API refused one of the three model ids. Do not substitute another."""

    def __init__(self, model_id: str, detail: str) -> None:
        self.model_id = model_id
        super().__init__(f"Model id rejected by API: {model_id}: {detail}")


def load_api_key() -> str:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path)
    key = os.environ.get("ASSIGNMENT_API_KEY", "").strip()
    if not key:
        raise SystemExit("ASSIGNMENT_API_KEY is missing")
    return key


def safe_error(exc: BaseException) -> str:
    text = _KEY_RE.sub("[redacted]", str(exc))
    return text[:600]


def get_llm(role: str) -> ChatOpenAI:
    model_id = MODELS[role]
    with _LOCK:
        client = _CLIENTS.get(model_id)
        if client is None:
            client = _make_client(model_id)
            _CLIENTS[model_id] = client
        return client


def invoke_structured[T: BaseModel](
    role: str, schema: type[T], system: str, user: str
) -> T:
    """Call ``role``'s model and parse a pydantic object. Retry transient failures."""
    model_id = MODELS[role]
    runnable = get_llm(role).with_structured_output(
        schema, method="json_schema", strict=True
    )
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    delay = 2.0
    last: BaseException | None = None
    for _ in range(3):
        try:
            result = runnable.invoke(messages)
        except _RETRYABLE as exc:
            last = exc
            time.sleep(delay)
            delay *= 2
            continue
        except APIError as exc:
            if _is_model_rejected(exc):
                raise ModelRejected(model_id, safe_error(exc)) from None
            if _is_fatal_request(exc):
                raise RuntimeError(
                    f"{model_id} rejected the request: {safe_error(exc)}"
                ) from None
            last = exc
            time.sleep(delay)
            delay *= 2
            continue
        if isinstance(result, schema):
            return result
        if isinstance(result, dict):
            return schema.model_validate(result)
        last = TypeError(type(result).__name__)
        time.sleep(delay)
    detail = safe_error(last) if last else "empty"
    raise RuntimeError(f"{model_id} failed after retries: {detail}")


def _make_client(model_id: str) -> ChatOpenAI:
    key = SecretStr(load_api_key())
    # gpt-5-nano only accepts the default temperature unless reasoning is off.
    # Low effort keeps the extraction bill down without skipping the answer.
    if model_id.startswith("gpt-5"):
        return ChatOpenAI(
            model=model_id,
            api_key=key,
            timeout=300,
            max_retries=2,
            reasoning_effort="low",
        )
    return ChatOpenAI(
        model=model_id,
        api_key=key,
        timeout=180,
        max_retries=2,
        temperature=0,
    )


def _is_model_rejected(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    if "modelnotfound" in name or "notfound" in name:
        return True
    text = str(exc).lower()
    if "model" not in text:
        return False
    markers = (
        "does not exist",
        "do not exist",
        "not found",
        "model_not_found",
        "invalid model",
        "unknown model",
    )
    return any(marker in text for marker in markers)


def _is_fatal_request(exc: BaseException) -> bool:
    text = str(exc).lower()
    if "invalid schema" in text or "invalid_json_schema" in text:
        return True
    return "authentication" in type(exc).__name__.lower()
