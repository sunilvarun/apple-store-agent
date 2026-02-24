from fastapi import APIRouter, HTTPException, Query

from catalog.catalog_store import catalog_store

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("")
def get_catalog(
    series: str | None = Query(None),
    max_price: int | None = Query(None),
    tier: str | None = Query(None),
):
    products = catalog_store.get_all(series=series, max_price=max_price)
    if tier:
        products = [p for p in products if p.tier == tier]
    return {"products": [p.model_dump() for p in products], "total": len(products)}


@router.get("/compare")
def compare_catalog(models: str = Query(..., description="Comma-separated model slugs")):
    slugs = [s.strip() for s in models.split(",")]
    products = [catalog_store.get_by_slug(s) for s in slugs]
    missing = [slugs[i] for i, p in enumerate(products) if p is None]
    if missing:
        raise HTTPException(status_code=404, detail=f"Models not found: {missing}")
    return {"products": [p.model_dump() for p in products if p]}


@router.get("/{model_slug}")
def get_product(model_slug: str):
    product = catalog_store.get_by_slug(model_slug)
    if not product:
        raise HTTPException(status_code=404, detail=f"Model '{model_slug}' not found")
    review_scores = catalog_store.get_review_scores(model_slug)
    return {"product": product.model_dump(), "review_scores": review_scores}
