"""
Loads iPhone catalog from JSON and review aspect scores.
Provides filtering and lookup used by tool handlers.
"""

import json
from pathlib import Path

from models.product import IPhoneProduct


class CatalogStore:
    def __init__(self):
        self._products: list[IPhoneProduct] = []
        self._review_scores: dict = {}
        self._review_quotes: dict = {}

    def load(self, catalog_path: Path, review_scores_path: Path):
        # Load product catalog
        data = json.loads(catalog_path.read_text())
        self._products = [IPhoneProduct(**p) for p in data["products"]]
        print(f"  Loaded {len(self._products)} products from catalog")

        # Load review aspect scores (optional — app works without it)
        if review_scores_path.exists():
            self._review_scores = json.loads(review_scores_path.read_text())
            print(f"  Loaded review scores for {len(self._review_scores)} models")
        else:
            print(f"  [WARN] Review scores not found at {review_scores_path} — using specs only")

        # Load review quotes (same directory as scores)
        quotes_path = review_scores_path.parent / "review_quotes.json"
        if quotes_path.exists():
            self._review_quotes = json.loads(quotes_path.read_text())
            print(f"  Loaded review quotes for {len(self._review_quotes)} models")

    def get_all(self, series: str | None = None, max_price: int | None = None) -> list[IPhoneProduct]:
        results = self._products
        if series:
            results = [p for p in results if series.lower() in p.series.lower()]
        if max_price:
            results = [p for p in results if p.starting_price <= max_price]
        return results

    def get_by_slug(self, slug: str) -> IPhoneProduct | None:
        return next((p for p in self._products if p.model_slug == slug), None)

    def get_review_scores(self, model_slug: str) -> dict:
        return self._review_scores.get(model_slug, {})

    def get_review_quotes(self, model_slug: str) -> dict:
        return self._review_quotes.get(model_slug, {})

    def get_all_review_scores(self) -> dict:
        return self._review_scores

    @property
    def product_count(self) -> int:
        return len(self._products)


# Singleton instance shared across the app
catalog_store = CatalogStore()
