Chunking walks every `.py` file under `AI4SE_Playground` (the package and the tests, 27 files) with Python's `ast`.

Each file yields one module header: the module docstring, imports, assignments, and the `TYPE_CHECKING` import block. `if __name__ == "__main__"` is omitted because it only launches `unittest`.

Each class yields one class header: decorators, the class line, the docstring, class-level attributes, and method signatures. Method bodies are replaced with `...`. Nested classes get their own header. Each function and each method is its own chunk, including stubs whose body is only `pass` or `NotImplementedError`, and including functions nested inside methods. The text is the original source from the first decorator through the end of the body.

Every chunk starts with `# <path> :: <qualname>`, for example `# playground/playground/orders.py :: Order.__len__`. The model is a pydantic `Chunk` (`id`, `file`, `qualname`, `kind`, `start_line`, `end_line`, `text`).

The chunk size is one AST node, not a fixed token window. A coding task needs a whole function, or the shape of a class. A safety split still exists: if `len(text) / 4` exceeds 1500 tokens (6000 characters), the chunk is cut by lines with a 4-line overlap, and each part repeats the location comment. That split did not run.

Measured (`uv run python -m rag.chunk`), stored in `rag/data/chunks.json` (511270 bytes):

- 828 chunks
- class_header 103, method 665, function 33, module_header 27
- characters: mean 317.0, median 269.0, max 1943 (about 486 tokens)
- parts created by the 1500-token split: 0
