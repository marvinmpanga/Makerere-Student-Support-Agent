"""W3-03: Document ingestion, semantic chunking and ChromaDB vector indexing.

Pipeline:  source_register.json -> PDF text extraction (per page) -> token-window
chunking (512 tokens, 10% overlap) -> embeddings -> persistent ChromaDB collection.

Every chunk stores ``doc_id``, ``title``, ``page_start``/``page_end`` and a ready-made
``citation`` tag of the form ``[Doc_ID, Page N]`` so the retriever (W3-04) can inject
precise, traceable citations.

Usage::

    python -m src.rag.ingest                    # Gemini embeddings (needs GEMINI_API_KEY)
    python -m src.rag.ingest --embedder hash    # offline deterministic embeddings (tests/CI)
    python -m src.rag.ingest --limit 3 --reset
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger("rag.ingest")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTER = PROJECT_ROOT / "knowledge" / "source_register.json"
DEFAULT_VECTORSTORE = Path(__file__).resolve().parent / "vectorstore"
COLLECTION_NAME = "makerere_policies"

CHUNK_TOKENS = 512
OVERLAP_RATIO = 0.10
EMBED_BATCH_SIZE = 20
EMBED_MAX_RETRIES = 8
GEMINI_EMBED_MODEL = "gemini-embedding-001"

_TOKEN_RE = re.compile(r"\S+")


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    category: str
    text: str
    page_start: int
    page_end: int
    chunk_index: int
    source_url: str = ""

    @property
    def citation(self) -> str:
        if self.page_start == self.page_end:
            return f"[{self.doc_id}, Page {self.page_start}]"
        return f"[{self.doc_id}, Pages {self.page_start}-{self.page_end}]"

    def metadata(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "category": self.category,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "chunk_index": self.chunk_index,
            "source_url": self.source_url,
            "citation": self.citation,
        }


@dataclass
class IngestReport:
    documents_indexed: int = 0
    chunks_indexed: int = 0
    embedder: str = ""
    indexed_documents: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "collection_name": COLLECTION_NAME,
            "chunk_tokens": CHUNK_TOKENS,
            "overlap_ratio": OVERLAP_RATIO,
            "embedder": self.embedder,
            "documents_indexed": self.documents_indexed,
            "chunks_indexed": self.chunks_indexed,
            "indexed_documents": self.indexed_documents,
            "skipped": self.skipped,
        }


# --------------------------------------------------------------------------- #
# Embedding backends
# --------------------------------------------------------------------------- #
class Embedder(Protocol):
    name: str

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class GeminiEmbedder:
    """Gemini embeddings via the ``google-genai`` SDK."""

    name = f"gemini:{GEMINI_EMBED_MODEL}"

    def __init__(self, api_key: str | None = None, model: str = GEMINI_EMBED_MODEL) -> None:
        key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("LLM_API_KEY")
        )
        if not key:
            raise ValueError("GEMINI_API_KEY (or LLM_API_KEY) must be set to use Gemini embeddings")
        from google import genai  # imported lazily so offline/test runs need no key

        self._client = genai.Client(api_key=key)
        self._model = model

    def _embed(self, texts: Sequence[str], task_type: str) -> list[list[float]]:
        import time

        from google.genai import errors, types

        for attempt in range(1, EMBED_MAX_RETRIES + 1):
            try:
                response = self._client.models.embed_content(
                    model=self._model,
                    contents=list(texts),
                    config=types.EmbedContentConfig(task_type=task_type),
                )
                return [list(e.values) for e in response.embeddings]
            except errors.ClientError as exc:
                if getattr(exc, "code", None) != 429 or attempt == EMBED_MAX_RETRIES:
                    raise
                wait = min(15 * attempt, 90)
                logger.warning("Rate limited (429); retry %d in %ds", attempt, wait)
                time.sleep(wait)
        raise RuntimeError("unreachable")  # pragma: no cover

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]


class HashEmbedder:
    """Deterministic, offline bag-of-words hashing embedder (tests and CI only)."""

    name = "hash:v1"

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.md5(word.encode(), usedforsecurity=False).digest()
            vec[int.from_bytes(digest[:4], "big") % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


class LocalEmbedder:
    """Local semantic embeddings (all-MiniLM-L6-v2 via ONNX, bundled with ChromaDB).

    Free, offline after the one-off model download (~80MB) and needs no API key.
    Note: MiniLM truncates input at ~256 word-pieces, so only the start of each
    512-token chunk influences its vector.
    """

    name = "local:all-MiniLM-L6-v2"

    def __init__(self) -> None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self._fn = DefaultEmbeddingFunction()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [[float(x) for x in v] for v in self._fn(list(texts))]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def get_embedder(kind: str = "gemini") -> Embedder:
    if kind == "gemini":
        return GeminiEmbedder()
    if kind == "local":
        return LocalEmbedder()
    if kind == "hash":
        return HashEmbedder()
    raise ValueError(f"Unknown embedder: {kind!r}")


# --------------------------------------------------------------------------- #
# Extraction & chunking
# --------------------------------------------------------------------------- #
def load_register(path: Path = DEFAULT_REGISTER) -> list[dict[str, Any]]:
    """Return register entries that point at a local file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [d for d in data.get("documents", []) if d.get("local_path")]


def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Return ``[(page_number, text), ...]`` (1-based) for pages that contain text."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, str]] = []
    for number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001 - one bad page must not kill the document
            logger.warning("%s page %d unreadable: %s", pdf_path.name, number, exc)
            continue
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            pages.append((number, text))
    return pages


def chunk_pages(
    pages: Sequence[tuple[int, str]],
    chunk_tokens: int = CHUNK_TOKENS,
    overlap_ratio: float = OVERLAP_RATIO,
) -> list[tuple[str, int, int]]:
    """Slide a token window across the document, tracking the pages each chunk spans.

    Tokens are whitespace-delimited words (a dependency-free, deterministic proxy for
    model tokens). Returns ``[(text, page_start, page_end), ...]``.
    """
    if chunk_tokens <= 0 or not 0 <= overlap_ratio < 1:
        raise ValueError("chunk_tokens must be > 0 and overlap_ratio in [0, 1)")

    tokens: list[str] = []
    token_pages: list[int] = []
    for page_number, text in pages:
        for match in _TOKEN_RE.finditer(text):
            tokens.append(match.group())
            token_pages.append(page_number)

    if not tokens:
        return []

    stride = max(1, chunk_tokens - int(chunk_tokens * overlap_ratio))
    chunks: list[tuple[str, int, int]] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_tokens, len(tokens))
        chunks.append((" ".join(tokens[start:end]), token_pages[start], token_pages[end - 1]))
        if end == len(tokens):
            break
        start += stride
    return chunks


def build_chunks(entry: dict[str, Any], pdf_path: Path) -> list[Chunk]:
    pages = extract_pages(pdf_path)
    doc_id = entry["id"]
    return [
        Chunk(
            chunk_id=f"{doc_id}::c{index:04d}",
            doc_id=doc_id,
            title=entry.get("title", doc_id),
            category=entry.get("category", ""),
            text=text,
            page_start=p_start,
            page_end=p_end,
            chunk_index=index,
            source_url=entry.get("source_url", ""),
        )
        for index, (text, p_start, p_end) in enumerate(chunk_pages(pages))
    ]


# --------------------------------------------------------------------------- #
# Vector store
# --------------------------------------------------------------------------- #
def get_collection(persist_dir: Path = DEFAULT_VECTORSTORE, reset: bool = False):
    import chromadb

    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception as exc:  # noqa: BLE001 - collection may not exist yet
            logger.debug("No existing collection to reset: %s", exc)
    return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def index_chunks(collection, chunks: Sequence[Chunk], embedder: Embedder) -> int:
    """Embed and upsert chunks (idempotent per ``chunk_id``). Returns chunks written."""
    written = 0
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        collection.upsert(
            ids=[c.chunk_id for c in batch],
            documents=[c.text for c in batch],
            embeddings=embedder.embed_documents([c.text for c in batch]),
            metadatas=[c.metadata() for c in batch],
        )
        written += len(batch)
    return written


def ingest(
    register_path: Path = DEFAULT_REGISTER,
    persist_dir: Path = DEFAULT_VECTORSTORE,
    embedder: Embedder | None = None,
    reset: bool = False,
    limit: int | None = None,
    root: Path = PROJECT_ROOT,
) -> IngestReport:
    """Run the full ingestion pipeline and return a report."""
    embedder = embedder or get_embedder("gemini")
    collection = get_collection(persist_dir, reset=reset)
    report = IngestReport(embedder=embedder.name)

    entries = load_register(register_path)
    if limit:
        entries = entries[:limit]

    for entry in entries:
        doc_id = entry["id"]
        pdf_path = root / entry["local_path"]
        if not pdf_path.is_file():
            report.skipped.append({"doc_id": doc_id, "reason": "file not found"})
            logger.warning("%s: file not found (%s)", doc_id, pdf_path)
            continue
        try:
            chunks = build_chunks(entry, pdf_path)
        except Exception as exc:  # noqa: BLE001 - corrupt PDF: record and continue
            report.skipped.append({"doc_id": doc_id, "reason": f"extract failed: {exc}"})
            logger.warning("%s: extraction failed: %s", doc_id, exc)
            continue
        if not chunks:
            report.skipped.append({"doc_id": doc_id, "reason": "no extractable text (scanned?)"})
            logger.warning("%s: no extractable text", doc_id)
            continue

        # Drop stale chunks so re-ingesting a shrunken document leaves no orphans.
        collection.delete(where={"doc_id": doc_id})
        written = index_chunks(collection, chunks, embedder)
        report.chunks_indexed += written
        report.documents_indexed += 1
        report.indexed_documents.append(
            {
                "doc_id": doc_id,
                "title": entry.get("title", doc_id),
                "category": entry.get("category", ""),
                "chunks": written,
                "page_span": f"{chunks[0].page_start}-{chunks[-1].page_end}",
                "sample_citation": chunks[0].citation,
                "source_url": entry.get("source_url", ""),
            }
        )
        logger.info("%s: %d chunks", doc_id, len(chunks))

    manifest_path = Path(persist_dir) / "index_manifest.json"
    manifest_path.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest Makerere policies into ChromaDB")
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--persist-dir", type=Path, default=DEFAULT_VECTORSTORE)
    parser.add_argument("--embedder", choices=["gemini", "local", "hash"], default="gemini")
    parser.add_argument("--reset", action="store_true", help="drop the collection first")
    parser.add_argument("--limit", type=int, default=None, help="only first N documents")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

    report = ingest(
        register_path=args.register,
        persist_dir=args.persist_dir,
        embedder=get_embedder(args.embedder),
        reset=args.reset,
        limit=args.limit,
    )
    print(json.dumps(report.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
