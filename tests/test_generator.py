from abap_rag.generator import PromptGenerator
from abap_rag.models import DocumentChunk, RetrievedChunk


def test_generator_with_context() -> None:
    chunk = DocumentChunk(chunk_id="1", source="x", title="t", text="ABAP SELECT example")
    out = PromptGenerator.generate("how to query", [RetrievedChunk(chunk=chunk, score=0.9)])
    assert "Question:" in out
    assert "ABAP SELECT example" in out
