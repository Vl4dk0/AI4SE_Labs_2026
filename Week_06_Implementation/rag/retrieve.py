"""Exact nearest-neighbour search over the stored chunk vectors.

A few hundred rows are cheaper to scan than to index. Cosine similarity
on L2-normalized vectors is their dot product.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import numpy as np
from numpy.typing import NDArray

from rag.chunk import Chunk
from rag.embed import (
    DIMS,
    EMBEDDINGS_PATH,
    META_PATH,
    MODEL,
    StoreMeta,
    chunks_sha256,
    embed_texts,
    load_chunks,
)

_index: tuple[list[Chunk], NDArray[np.float32]] | None = None


def load_index() -> tuple[list[Chunk], NDArray[np.float32]]:
    """Load chunks and vectors, refusing a matrix that was built for other chunks."""
    global _index
    if _index is not None:
        return _index
    if not EMBEDDINGS_PATH.is_file() or not META_PATH.is_file():
        raise SystemExit("embedding store is missing; run python -m rag.embed")
    meta = StoreMeta.model_validate(json.loads(META_PATH.read_text(encoding="utf-8")))
    if meta.chunks_sha256 != chunks_sha256():
        raise SystemExit("embedding store is stale; run python -m rag.embed")
    if meta.model != MODEL or meta.dims != DIMS:
        raise SystemExit("embedding store used a different model; run python -m rag.embed")
    chunks = load_chunks()
    loaded: object = np.load(EMBEDDINGS_PATH)
    matrix = np.asarray(loaded, dtype=np.float32)
    if matrix.shape != (meta.chunk_count, DIMS) or len(chunks) != meta.chunk_count:
        raise SystemExit("embedding store does not match chunks.json; run python -m rag.embed")
    _index = (chunks, matrix)
    return _index


def top_n(query_vec: NDArray[np.floating[Any]], n: int) -> list[tuple[Chunk, float]]:
    """Return the n chunks with the highest cosine similarity to query_vec."""
    chunks, matrix = load_index()
    if n <= 0 or len(chunks) == 0:
        return []
    query = np.asarray(query_vec, dtype=np.float32).reshape(-1)
    if query.shape != (DIMS,):
        raise ValueError(f"query vector must have length {DIMS}")
    norm = float(np.linalg.norm(query))
    if norm > 0:
        query = query / np.float32(norm)
    scores = matrix @ query
    k = min(n, int(scores.shape[0]))
    if k == scores.shape[0]:
        chosen = np.argsort(-scores)
    else:
        part = np.argpartition(-scores, k - 1)[:k]
        chosen = part[np.argsort(-scores[part])]
    return [(chunks[int(index)], float(scores[int(index)])) for index in chosen]


def retrieve(task_text: str, n: int = 5) -> list[tuple[Chunk, float]]:
    """Embed a task description and return the n closest chunks."""
    vector = embed_texts([task_text])[0]
    return top_n(vector, n)


def main() -> None:
    if len(sys.argv) != 2:
        print('usage: python -m rag.retrieve "query"', file=sys.stderr)
        raise SystemExit(2)
    for chunk, score in retrieve(sys.argv[1], n=5):
        print(f"{score:.4f}  {chunk.file} :: {chunk.qualname}")


if __name__ == "__main__":
    main()
