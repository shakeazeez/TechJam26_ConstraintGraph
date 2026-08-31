"""Catalog loading and participant-visible derived indexes."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .parsing import COLORS, MATERIALS, clean_text, infer_attribute


TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)
MATERIAL_RE = re.compile(rf"\b({'|'.join(map(re.escape, MATERIALS))})\b", re.I)
COLOR_RE = re.compile(rf"\b({'|'.join(map(re.escape, COLORS[:-1]))})\b", re.I)
SEARCH_FIELDS = ("title", "features", "details", "description", "categories", "store")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "i", "in", "is", "it",
    "me", "my", "of", "on", "or", "please", "some", "that", "the", "this", "to", "want", "with", "would",
    "you", "looking", "item", "product", "clothing", "shoes", "jewelry",
}


def normalize_phrase(value: str) -> str:
    value = clean_text(value).casefold()
    value = re.sub(r"\s*([:/,()])\s*", r"\1", value)
    return re.sub(r"\s+", " ", value)


def terms(value: str) -> tuple[str, ...]:
    return tuple(
        token.casefold()
        for token in TOKEN_RE.findall(value)
        if len(token) > 1 and token.casefold() not in STOPWORDS
    )


def flatten_values(value: object) -> list[str]:
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items() if item not in (None, "", [])]
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)] if value not in (None, "") else []


def searchable_text(product: dict) -> str:
    parts: list[str] = []
    for field in SEARCH_FIELDS:
        parts.extend(flatten_values(product.get(field)))
    return " ".join(parts).strip()


def derived_intent_values(product: dict, limit: int = 180) -> tuple[str, ...]:
    """Derive general shopping constraints from visible catalog fields only."""

    candidates = [*flatten_values(product.get("features")), *flatten_values(product.get("details"))]
    corpus = searchable_text(product)
    material = MATERIAL_RE.search(corpus)
    color = COLOR_RE.search(corpus)
    if material:
        candidates.insert(0, material.group(1).lower())
    if color:
        candidates.insert(1, f"color: {color.group(1).lower()}")
    if product.get("price") not in (None, ""):
        candidates.append(f"budget around ${product['price']}")

    cleaned: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        item = re.sub(r"\s+", " ", str(value)).strip(" -;,.\t\n")[:limit].rstrip()
        key = normalize_phrase(item)
        if item and key not in seen:
            seen.add(key)
            cleaned.append(item)
    if not cleaned:
        cleaned = [clean_text(str(product.get("title") or "product"))[:limit]]
    return tuple(cleaned[:4])


def coarse_category(values: Iterable[object]) -> str:
    excluded = {"clothing", "clothing shoes & jewelry", "clothing, shoes & jewelry"}
    cleaned: list[str] = []
    for value in values:
        for part in str(value).split(","):
            part = part.strip()
            if part and part.casefold() not in excluded:
                cleaned.append(part)
    return " ".join(cleaned[-2:]) if cleaned else "clothing item"


@dataclass(frozen=True, slots=True)
class ProductRecord:
    parent_asin: str
    title: str
    category: str
    category_terms: frozenset[str]
    title_terms: frozenset[str]
    content_terms: frozenset[str]
    lexical_document: str
    signatures: tuple[str, ...]
    attributes: dict[str, tuple[str, ...]]
    average_rating: float
    rating_number: int

    @property
    def popularity(self) -> float:
        return math.log1p(max(0, self.rating_number)) * max(0.0, self.average_rating)


class CatalogIndex:
    def __init__(self, products: list[ProductRecord]) -> None:
        self.products = products
        self.by_asin = {product.parent_asin: index for index, product in enumerate(products)}
        phrase_work: dict[str, set[int]] = defaultdict(set)
        category_work: dict[str, set[int]] = defaultdict(set)
        for index, product in enumerate(products):
            for signature in product.signatures:
                phrase_work[normalize_phrase(signature)].add(index)
            for token in product.category_terms | product.title_terms:
                category_work[token].add(index)
        self.phrase_postings = {key: frozenset(value) for key, value in phrase_work.items()}
        self.category_postings = {key: frozenset(value) for key, value in category_work.items()}
        self.popular_ids = tuple(
            sorted(range(len(products)), key=lambda item: (-products[item].popularity, products[item].parent_asin))
        )

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "CatalogIndex":
        products: list[dict] = []
        with Path(path).open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    products.append(json.loads(line))
        return cls.from_products(products)

    @classmethod
    def from_products(cls, rows: Iterable[dict]) -> "CatalogIndex":
        products: list[ProductRecord] = []
        for row in rows:
            signatures = derived_intent_values(row)
            attributes: dict[str, list[str]] = defaultdict(list)
            for signature in signatures:
                attributes[infer_attribute(signature)].append(signature)
            store = clean_text(str(row.get("store") or ""))
            if store:
                attributes["brand"].append(store)
            category = coarse_category(row.get("categories") or [])
            attributes["category"].append(category)
            title = clean_text(str(row.get("title") or ""))
            lexical_document = " ".join([title, title, category, category, *signatures, *signatures])
            products.append(
                ProductRecord(
                    parent_asin=str(row["parent_asin"]),
                    title=title,
                    category=category,
                    category_terms=frozenset(terms(" ".join(map(str, row.get("categories") or [])))),
                    title_terms=frozenset(terms(str(row.get("title") or ""))),
                    content_terms=frozenset(terms(" ".join([str(row.get("title") or ""), category, *signatures]))),
                    lexical_document=lexical_document,
                    signatures=signatures,
                    attributes={key: tuple(value) for key, value in attributes.items()},
                    average_rating=float(row.get("average_rating") or 0.0),
                    rating_number=int(row.get("rating_number") or 0),
                )
            )
        return cls(products)

    def category_candidates(self, query: str) -> set[int]:
        query_terms = terms(query)
        if not query_terms:
            return set()
        posting_sets = [set(self.category_postings[token]) for token in query_terms if token in self.category_postings]
        if not posting_sets:
            return set()
        intersection = set.intersection(*posting_sets)
        return intersection or set.union(*posting_sets)
