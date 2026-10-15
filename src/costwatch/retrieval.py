"""Local vector retrieval using SentenceTransformers and deterministic cosine ranking."""

from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from src.costwatch.notes import StructuredNote, load_structured_notes


class NoteRetriever:
    """Manages local note embeddings and similarity search."""

    def __init__(
        self,
        notes: Optional[List[StructuredNote]] = None,
        model_name: str = "all-MiniLM-L6-v2",
        embeddings_cache_path: str = "data/note_embeddings.npy",
        notes_json_path: str = "data/notes_structured.json",
    ):
        self.model_name = model_name
        self.cache_path = Path(embeddings_cache_path)
        self.notes_json_path = notes_json_path

        if notes is None:
            self.notes = load_structured_notes(notes_json_path)
        else:
            self.notes = notes

        self.model = SentenceTransformer(self.model_name)
        self.embeddings = self._get_or_compute_embeddings()

    def _get_or_compute_embeddings(self) -> np.ndarray:
        """Load embeddings from cache or compute and save them."""
        if self.cache_path.exists():
            try:
                emb = np.load(self.cache_path)
                if emb.shape[0] == len(self.notes):
                    return emb
            except Exception:
                pass

        # Compute embeddings for all notes
        texts = [f"{n.applies_to} ({n.date}): {n.original_text}" for n in self.notes]
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(self.cache_path, embeddings)
        return embeddings

    def retrieve(
        self,
        route: str,
        week_of: str,
        query: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Tuple[StructuredNote, float]]:
        """Retrieve notes relevant to route and week_of, ranked deterministically.
        
        Args:
            route: Candidate route name (e.g. "Chennai-Bangalore")
            week_of: Monday date of candidate week (e.g. "2025-02-24")
            query: Custom query or defaults to cost increase description
            top_k: Max notes to return
        Returns:
            List of (note, similarity_score) sorted by score desc, note_id asc.
        """
        if query is None:
            query = f"freight cost increase on {route} in week of {week_of}"

        query_vec = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]

        scored_candidates: List[Tuple[StructuredNote, float]] = []
        for idx, note in enumerate(self.notes):
            # Pre-filter by route metadata: must apply to "ALL" or match the route
            if note.routes != "ALL" and route not in note.routes:
                continue

            # Cosine similarity (already normalized vectors -> dot product)
            score = float(np.dot(query_vec, self.embeddings[idx]))
            scored_candidates.append((note, score))

        # Deterministic sorting: highest score first, tie-break by note_id ascending
        scored_candidates.sort(key=lambda x: (-x[1], x[0].note_id))

        return scored_candidates[:top_k]
