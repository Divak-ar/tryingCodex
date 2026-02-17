from __future__ import annotations

from .models import RetrievedChunk


class PromptGenerator:
    """Simple answer composer with citations from retrieved chunks."""

    @staticmethod
    def generate(query: str, contexts: list[RetrievedChunk]) -> str:
        if not contexts:
            return "No relevant ABAP documentation was found for this query."

        lines = [f"Question: {query}", "", "Relevant ABAP context:"]
        for i, row in enumerate(contexts, start=1):
            lines.append(f"[{i}] Source: {row.chunk.source} | Score: {row.score:.3f}")
            lines.append(row.chunk.text.replace("\n", " ")[:500])
            lines.append("")

        lines.append("Draft answer:")
        lines.append(
            "Use the context above to implement or explain SAP ABAP behavior. "
            "Validate with your ABAP release notes and system-specific customization."
        )
        return "\n".join(lines)
