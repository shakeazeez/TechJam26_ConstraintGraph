"""Lightweight in-memory BM25 and word/character TF-IDF indexes."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from ..catalog import CatalogIndex, terms
from ..state import ProjectedState


@dataclass(frozen=True, slots=True)
class LexicalScores:
    bm25: dict[int, float]
    word_tfidf: dict[int, float]
    char_tfidf: dict[int, float]


def state_query(state: ProjectedState, profile: dict | None = None) -> str:
    parts = [state.category or ""]
    parts.extend(state.values())
    if profile:
        parts.extend(map(str, profile.get("preference_tags") or []))
    return " ".join(part for part in parts if part).strip()


class LexicalIndex:
    def __init__(self, catalog: CatalogIndex) -> None:
        self.catalog = catalog
        documents = [product.lexical_document for product in catalog.products]
        word_min_df = 1 if len(documents) < 5 else 2
        char_min_df = 1 if len(documents) < 5 else 3
        self.word_vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            min_df=word_min_df,
            max_features=70_000,
            sublinear_tf=True,
            dtype=np.float32,
            norm="l2",
        )
        self.char_vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=char_min_df,
            max_features=45_000,
            sublinear_tf=True,
            dtype=np.float32,
            norm="l2",
        )
        self.word_matrix: csr_matrix = self.word_vectorizer.fit_transform(documents).tocsr()
        self.char_matrix: csr_matrix = self.char_vectorizer.fit_transform(documents).tocsr()
        self.connection = sqlite3.connect(":memory:")
        self._build_bm25()

    def _build_bm25(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE VIRTUAL TABLE docs USING fts5("
            "product_id UNINDEXED, title, category, signatures, "
            "tokenize='unicode61 remove_diacritics 2')"
        )
        cursor.executemany(
            "INSERT INTO docs VALUES (?, ?, ?, ?)",
            (
                (index, product.title, product.category, " ".join(product.signatures))
                for index, product in enumerate(self.catalog.products)
            ),
        )
        self.connection.commit()

    def _bm25(self, query: str, limit: int = 1000) -> dict[int, float]:
        unique_terms = list(dict.fromkeys(terms(query)))[:40]
        if not unique_terms:
            return {}
        expression = " OR ".join(f'"{re.sub(r"[^a-z0-9]", "", term)}"' for term in unique_terms if term)
        if not expression:
            return {}
        rows = self.connection.execute(
            "SELECT product_id, bm25(docs, 0.0, 5.0, 4.0, 3.0) AS score "
            "FROM docs WHERE docs MATCH ? ORDER BY score LIMIT ?",
            (expression, limit),
        ).fetchall()
        return {int(product_id): 1.0 / (60.0 + rank) for rank, (product_id, _) in enumerate(rows, start=1)}

    @staticmethod
    def _sparse_scores(matrix: csr_matrix, query_vector: csr_matrix, candidate_ids: np.ndarray) -> dict[int, float]:
        if query_vector.nnz == 0 or candidate_ids.size == 0:
            return {}
        values = (matrix[candidate_ids] @ query_vector.T).toarray().ravel()
        return {int(product_id): float(score) for product_id, score in zip(candidate_ids, values) if score > 0.0}

    def score(self, query: str, candidate_ids: Iterable[int]) -> LexicalScores:
        ids = np.fromiter(candidate_ids, dtype=np.int32)
        word_query = self.word_vectorizer.transform([query]).tocsr()
        char_query = self.char_vectorizer.transform([query]).tocsr()
        return LexicalScores(
            bm25=self._bm25(query),
            word_tfidf=self._sparse_scores(self.word_matrix, word_query, ids),
            char_tfidf=self._sparse_scores(self.char_matrix, char_query, ids),
        )
