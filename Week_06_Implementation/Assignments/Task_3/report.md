The embedding model is `flax-sentence-embeddings/st-codesearch-distilroberta-base`, width 768. It was trained on CodeSearchNet to match a description to source, and it is plain DistilRoBERTa, so it runs on this Mac with current transformers. Jina's code model needs custom code that does not import on transformers 5. The lab key also has no embedding model.

The embedded string is the chunk text. That text already starts with the file path and the qualified name.

Storage is `rag/data/embeddings.npy`, float32, row i aligned with `chunks.json`, each row L2-normalized. Measured row norms sit within 1e-6 of 1. `meta.json` stores the model, 768, chunk count 828, and the sha256 of `chunks.json`. The check matched: shape (828, 768), dtype float32, hash equal, count 828.

`uv run python -m rag.embed` used MPS. The first load took 40.44 s, which includes the download. Encoding the 828 chunks took 4.08 s and 84168 encoder tokens. Cost is $0. A later load from the local cache took 1.50 s. There is no vector database.
