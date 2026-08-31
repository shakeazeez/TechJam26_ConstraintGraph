"""Retrieval backends and fusion."""

from .exact import ExactRetriever, RetrievalResult
from .browsing import BrowsingRetriever

__all__ = ["BrowsingRetriever", "ExactRetriever", "RetrievalResult"]
