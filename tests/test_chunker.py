from abap_rag.chunker import chunk_document


def test_chunk_document_splits_text() -> None:
    text = "A" * 2000
    chunks = chunk_document("doc1", text, chunk_size=500, overlap=100)
    assert len(chunks) >= 4
    assert chunks[0].chunk_id.startswith("doc1:")


def test_chunk_validation() -> None:
    try:
        chunk_document("doc", "abc", chunk_size=50, overlap=50)
    except ValueError:
        assert True
    else:
        assert False
