"""Embed chunks with a local code model and store a matrix aligned to chunks.json.

The lab key can call chat models only, so the vectors are computed on this
machine. Rows are L2-normalized so search is a dot product. meta.json stores
the hash of chunks.json so a later re-chunk cannot use a stale matrix.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from typing import Protocol, cast

import numpy as np
import torch
from numpy.typing import NDArray
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from rag.chunk import CHUNKS_PATH, WEEK_ROOT, Chunk

# CodeSearchNet encoder: docstring text to source code. DistilRoBERTa, 768 dims, no custom code.
MODEL = "flax-sentence-embeddings/st-codesearch-distilroberta-base"
DIMS = 768
BATCH = 32

DATA_DIR = WEEK_ROOT / "rag" / "data"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npy"
META_PATH = DATA_DIR / "meta.json"

_encoder: SentenceTransformer | None = None


class _RunnableEncoder(Protocol):
    """The two calls we need. The library overloads are wider than this."""

    def encode(
        self,
        texts: list[str],
        *,
        batch_size: int,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> object: ...

    def tokenize(self, texts: list[str]) -> dict[str, torch.Tensor]: ...


class StoreMeta(BaseModel):
    """Which chunks and model a matrix belongs to, so a stale file is obvious."""

    model: str
    dims: int
    chunk_count: int
    chunks_sha256: str


def chunks_sha256() -> str:
    return hashlib.sha256(CHUNKS_PATH.read_bytes()).hexdigest()


def load_chunks() -> list[Chunk]:
    payload: object = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError("chunks.json must be a list")
    chunks: list[Chunk] = []
    for item in cast(list[object], payload):
        if not isinstance(item, dict):
            raise TypeError("chunk entry must be an object")
        chunks.append(Chunk.model_validate(item))
    return chunks


def _device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _model() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer(MODEL, device=_device())
    return _encoder


def _l2_normalize(matrix: NDArray[np.float32]) -> NDArray[np.float32]:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe = np.maximum(norms, np.float32(1e-12)).astype(np.float32, copy=False)
    return np.divide(matrix, safe, dtype=np.float32)


def embed_texts(texts: list[str]) -> NDArray[np.float32]:
    """Embed query or chunk texts with the same local model and width as the index."""
    if not texts:
        return np.zeros((0, DIMS), dtype=np.float32)
    encoded = cast(_RunnableEncoder, _model()).encode(
        texts,
        batch_size=BATCH,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    matrix = np.asarray(encoded, dtype=np.float32)
    if matrix.ndim == 1:
        matrix = matrix.reshape(1, -1)
    if matrix.shape != (len(texts), DIMS):
        raise RuntimeError(f"expected shape {(len(texts), DIMS)}, got {matrix.shape}")
    return _l2_normalize(matrix)


def token_count(texts: list[str]) -> int:
    """Count encoder tokens so the report can say how much text was embedded."""
    features = cast(_RunnableEncoder, _model()).tokenize(texts)
    return int(features["attention_mask"].sum())


def write_store(chunks: list[Chunk], matrix: NDArray[np.float32]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_PATH, matrix)
    meta = StoreMeta(
        model=MODEL,
        dims=DIMS,
        chunk_count=len(chunks),
        chunks_sha256=chunks_sha256(),
    )
    META_PATH.write_text(json.dumps(meta.model_dump(), indent=2) + "\n", encoding="utf-8")


def build_store() -> None:
    chunks = load_chunks()
    texts = [chunk.text for chunk in chunks]
    started = time.perf_counter()
    model = _model()
    load_seconds = time.perf_counter() - started
    started = time.perf_counter()
    matrix = embed_texts(texts)
    embed_seconds = time.perf_counter() - started
    tokens = token_count(texts)
    write_store(chunks, matrix)
    norms = np.linalg.norm(matrix, axis=1)
    print(f"model: {MODEL}")
    print(f"device: {model.device}")
    print(f"embedded {len(chunks)} chunks, dims={DIMS}")
    print(f"load_seconds={load_seconds:.2f} embed_seconds={embed_seconds:.2f}")
    print(f"encoder tokens: {tokens}")
    print("cost: $0 (local)")
    print(f"row norm min={float(norms.min()):.6f} max={float(norms.max()):.6f}")
    print(f"wrote {EMBEDDINGS_PATH.relative_to(WEEK_ROOT)} and {META_PATH.relative_to(WEEK_ROOT)}")


def main() -> None:
    if len(sys.argv) != 1:
        print("usage: python -m rag.embed", file=sys.stderr)
        raise SystemExit(2)
    build_store()


if __name__ == "__main__":
    main()
