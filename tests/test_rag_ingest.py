"""Tests for W3-03 ingestion, chunking and vector indexing (offline: hash embedder)."""

from __future__ import annotations

import json

from src.rag import ingest as ing


def _pages(n_words_per_page: list[int]) -> list[tuple[int, str]]:
    counter = 0
    pages = []
    for number, count in enumerate(n_words_per_page, start=1):
        words = [f"w{counter + i}" for i in range(count)]
        counter += count
        pages.append((number, " ".join(words)))
    return pages


def test_chunk_size_and_ten_percent_overlap():
    chunks = ing.chunk_pages(_pages([2000]))
    sizes = [len(c[0].split()) for c in chunks]
    assert all(s <= 512 for s in sizes)
    assert sizes[0] == 512
    first, second = chunks[0][0].split(), chunks[1][0].split()
    overlap = len(set(first) & set(second))
    assert overlap == 512 - (512 - int(512 * 0.10))  # 51 tokens
    assert 0.09 <= overlap / 512 <= 0.11


def test_chunks_cover_all_tokens():
    pages = _pages([700, 700])
    chunks = ing.chunk_pages(pages)
    seen = set()
    for text, _, _ in chunks:
        seen.update(text.split())
    assert len(seen) == 1400


def test_page_tracking_spans_boundary():
    chunks = ing.chunk_pages(_pages([300, 300]))
    assert chunks[0][1] == 1 and chunks[0][2] == 2


def test_empty_and_invalid_inputs():
    assert ing.chunk_pages([]) == []
    try:
        ing.chunk_pages(_pages([10]), chunk_tokens=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_citation_format():
    c = ing.Chunk("d::c0", "mak-policy-0002", "T", "cat", "x", 4, 4, 0)
    assert c.citation == "[mak-policy-0002, Page 4]"
    c2 = ing.Chunk("d::c1", "mak-policy-0002", "T", "cat", "x", 4, 5, 1)
    assert c2.citation == "[mak-policy-0002, Pages 4-5]"


def test_hash_embedder_deterministic_and_normalised():
    e = ing.HashEmbedder()
    a, b = e.embed_query("tuition fees"), e.embed_query("tuition fees")
    assert a == b
    assert abs(sum(v * v for v in a) - 1.0) < 1e-9


def _make_pdf(path, texts):
    from pypdf import PdfWriter
    from pypdf.generic import (
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
    )

    writer = PdfWriter()
    for text in texts:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
        )
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    with open(path, "wb") as fh:
        writer.write(fh)


def test_end_to_end_ingest_and_query(tmp_path):
    pdf_dir = tmp_path / "raw"
    pdf_dir.mkdir()
    _make_pdf(pdf_dir / "fees.pdf", ["Tuition must be paid before results", "Late fees apply"])
    _make_pdf(pdf_dir / "hostel.pdf", ["Hostel accommodation allocation rules"])
    register = tmp_path / "register.json"
    register.write_text(
        json.dumps(
            {
                "documents": [
                    {"id": "inst", "title": "No file", "category": "x", "authority": "y"},
                    {"id": "d-fees", "title": "Fees", "category": "fin", "authority": "M",
                     "local_path": "raw/fees.pdf", "source_url": "https://x/fees"},
                    {"id": "d-host", "title": "Hostel", "category": "stu", "authority": "M",
                     "local_path": "raw/hostel.pdf"},
                    {"id": "d-miss", "title": "Missing", "category": "x", "authority": "M",
                     "local_path": "raw/missing.pdf"},
                ]
            }
        ),
        encoding="utf-8",
    )
    store = tmp_path / "vs"
    emb = ing.HashEmbedder()

    report = ing.ingest(register, store, emb, reset=True, root=tmp_path)
    assert report.documents_indexed == 2
    assert report.skipped == [{"doc_id": "d-miss", "reason": "file not found"}]

    col = ing.get_collection(store)
    count = col.count()
    assert count == report.chunks_indexed > 0

    res = col.query(query_embeddings=[emb.embed_query("tuition results")], n_results=1)
    meta = res["metadatas"][0][0]
    assert meta["doc_id"] == "d-fees"
    assert meta["citation"].startswith("[d-fees, Page")
    assert meta["source_url"] == "https://x/fees"

    # Idempotent: re-ingesting does not duplicate chunks.
    ing.ingest(register, store, emb, root=tmp_path)
    assert ing.get_collection(store).count() == count
