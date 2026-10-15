# Architectural & Design Decisions

This document records deliberate design decisions, trade-offs, and clarifications made throughout implementation.

- **Python Environment (Python 3.12)**: Used Python 3.12 (`/Users/amarkp/.local/bin/python3.12`) to ensure compatibility across `torch`, `sentence-transformers`, `google-genai`, `pandas`, and `streamlit`.
- **Vector Retrieval Architecture**: Notes corpus contains 10 items. Embedding with `all-MiniLM-L6-v2` and computing cosine similarity via numpy array operations is deterministic, lightweight, fast (<1ms), and zero-dependency compared to heavyweight vector databases like Chroma/Pinecone.
- **Deterministic Guardrail Prioritization**: Retrieval proposes candidates ranked by similarity, but the deterministic applicability gate in `verdict.py` (matching route, temporal overlap, and effect) strictly decides justification.
