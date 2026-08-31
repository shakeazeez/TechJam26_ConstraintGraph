"""Retrieval backends and fusion."""

from .exact import ExactRetriever, RetrievalResult
from .browsing import BrowsingRetriever
from .hybrid import HybridRetriever
from .lexical import LexicalIndex

__all__ = ["BrowsingRetriever", "ExactRetriever", "HybridRetriever", "LexicalIndex", "RetrievalResult"]
