"""
Tool handler implementations for the Claude agent.
Each handler receives the tool input dict and returns a plain dict result.
"""

from catalog.catalog_store import catalog_store


# ---------------------------------------------------------------------------
# Spec-derived scores (normalised 0-1) for ranking
# ---------------------------------------------------------------------------

def _spec_camera_score(p) -> float:
    """Higher = better camera system."""
    score = 0.0
    zoom = {"5x": 1.0, "2x": 0.4}.get(p.max_optical_zoom, 0.4)
    score += zoom * 0.4
    mp = sum(c.megapixels for c in p.rear_cameras)
    score += min(1.0, mp / 120) * 0.3
    if any("ProRes" in (p.video_max or "") for _ in [1]):
        score += 0.2
    score += 0.1 if len(p.rear_cameras) >= 3 else 0.0
    return round(min(1.0, score), 3)


def _spec_battery_score(p) -> float:
    max_hrs = 35
    return round(min(1.0, p.battery_hours_video / max_hrs), 3)


def _spec_performance_score(p) -> float:
    return 1.0 if "Pro" in p.chip else 0.75


def _spec_display_score(p) -> float:
    score = 0.0
    if "ProMotion" in p.display_type:
        score += 0.4
    if "Always-On" in p.display_type:
        score += 0.2
    score += min(0.4, p.display_brightness_nits / 5000)
    return round(score, 3)


def _spec_weight_score(p) -> float:
    """Lower weight → higher score."""
    return round(max(0.0, 1.0 - (p.weight_grams - 140) / 100), 3)


def _spec_value_score(p) -> float:
    """Lower starting price → higher value score."""
    return round(max(0.0, 1.0 - (p.starting_price - 799) / 800), 3)


SPEC_SCORERS = {
    "camera":      _spec_camera_score,
    "battery":     _spec_battery_score,
    "performance": _spec_performance_score,
    "display":     _spec_display_score,
    "weight":      _spec_weight_score,
    "value":       _spec_value_score,
}


def _blended_score(model_slug: str, aspect: str) -> dict:
    """Return blended spec+review score and evidence for one aspect."""
    product = catalog_store.get_by_slug(model_slug)
    review_scores = catalog_store.get_review_scores(model_slug)

    spec_fn = SPEC_SCORERS.get(aspect)
    spec_score = spec_fn(product) if spec_fn and product else 0.5

    review = review_scores.get(aspect, {})
    review_score = review.get("score", 0.5)
    confidence = review.get("confidence", 0.0)
    volume = review.get("volume", 0)

    # Blend: spec 60%, review 40% (weighted by confidence)
    blended = spec_score * 0.6 + review_score * confidence * 0.4 + spec_score * (1 - confidence) * 0.4
    return {
        "blended": round(blended, 3),
        "spec_score": spec_score,
        "review_score": review_score if confidence > 0 else None,
        "review_volume": volume,
        "review_confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def handle_extract_preferences(inp: dict) -> dict:
    """Pass-through — Claude fills this in, we just echo it back with defaults."""
    prefs = {
        "budget_max": inp.get("budget_max"),
        "priorities": inp.get("priorities", {}),
        "usage": inp.get("usage", {}),
        "constraints": inp.get("constraints", {}),
        "apps": inp.get("apps", []),
    }
    return {"preferences": prefs, "status": "extracted"}


def handle_search_catalog(inp: dict) -> dict:
    query = inp.get("query", "").lower()
    products = catalog_store.get_all(
        series=inp.get("series"),
        max_price=inp.get("max_price"),
    )
    if inp.get("tier"):
        products = [p for p in products if p.tier == inp["tier"]]

    # Simple keyword scoring
    keywords = query.split()
    scored = []
    for p in products:
        score = 0
        searchable = f"{p.display_name} {p.chip} {p.tier} {p.video_max}".lower()
        for kw in keywords:
            if kw in searchable:
                score += 1
        if "camera" in query and p.tier == "pro":   score += 3
        if "gaming" in query and "Pro" in p.chip:   score += 2
        if "light" in query or "thin" in query:     score += (230 - p.weight_grams) // 20
        if "cheap" in query or "budget" in query:   score += (1200 - p.starting_price) // 100
        scored.append((score, p))

    scored.sort(key=lambda x: -x[0])
    return {
        "results": [
            {
                "model_slug": p.model_slug,
                "display_name": p.display_name,
                "starting_price": p.starting_price,
                "chip": p.chip,
                "camera_count": len(p.rear_cameras),
                "max_zoom": p.max_optical_zoom,
                "battery_hours": p.battery_hours_video,
                "weight_grams": p.weight_grams,
                "tier": p.tier,
            }
            for _, p in scored
        ]
    }


def handle_get_product_details(inp: dict) -> dict:
    slug = inp.get("model_slug", "")
    product = catalog_store.get_by_slug(slug)
    if not product:
        return {"error": f"Model '{slug}' not found. Available: {[p.model_slug for p in catalog_store.get_all()]}"}

    review_scores = catalog_store.get_review_scores(slug)

    return {
        "product": product.model_dump(),
        "review_scores": review_scores,
        "review_summary": {
            aspect: {
                "score": data.get("score"),
                "sentiment": "positive" if data.get("score", 0.5) > 0.55 else "mixed",
                "volume": data.get("volume"),
                "confidence": data.get("confidence"),
            }
            for aspect, data in review_scores.items()
        }
    }


def handle_rank_iphones(inp: dict) -> dict:
    prefs = inp.get("preferences", {})
    priorities = prefs.get("priorities", {})
    budget_max = prefs.get("budget_max")
    constraints = prefs.get("constraints", {})
    min_storage_gb = constraints.get("min_storage_gb", 0)
    must_have = constraints.get("must_have", [])
    size_pref = constraints.get("size_preference", "any")

    candidates = catalog_store.get_all(max_price=budget_max)

    # Apply candidate slug filter if provided
    candidate_slugs = inp.get("candidate_slugs", [])
    if candidate_slugs:
        candidates = [p for p in candidates if p.model_slug in candidate_slugs]

    # Filter: minimum storage
    if min_storage_gb:
        storage_map = {"128GB": 128, "256GB": 256, "512GB": 512, "1TB": 1024}
        candidates = [
            p for p in candidates
            if any(storage_map.get(t.capacity, 0) >= min_storage_gb for t in p.storage_tiers)
        ]

    # Filter: must_have features
    for feature in must_have:
        f = feature.lower()
        if "telephoto" in f:
            candidates = [p for p in candidates if any("Telephoto" in c.label for c in p.rear_cameras)]
        if "prores" in f or "pro res" in f:
            candidates = [p for p in candidates if "ProRes" in p.video_max]
        if "promotion" in f or "120hz" in f:
            candidates = [p for p in candidates if "ProMotion" in p.display_type]
        if "usb3" in f or "usb 3" in f:
            candidates = [p for p in candidates if "USB 3" in p.connector]

    # Filter: size preference
    if size_pref == "compact":
        candidates = [p for p in candidates if p.display_size <= 6.3]
    elif size_pref == "large":
        candidates = [p for p in candidates if p.display_size >= 6.6]

    if not candidates:
        return {"error": "No phones match the given constraints. Try relaxing budget or requirements."}

    # Score each candidate
    ranked = []
    for product in candidates:
        total_score = 0.0
        score_breakdown = {}

        for aspect, weight in priorities.items():
            if weight <= 0:
                continue
            evidence = _blended_score(product.model_slug, aspect)
            aspect_score = evidence["blended"]
            total_score += aspect_score * weight
            score_breakdown[aspect] = {
                "weighted_score": round(aspect_score * weight, 3),
                "raw_score": evidence["blended"],
                "spec_score": evidence["spec_score"],
                "review_score": evidence["review_score"],
                "review_volume": evidence["review_volume"],
            }

        priority_sum = sum(v for v in priorities.values() if v > 0)
        normalized = total_score / priority_sum if priority_sum > 0 else 0.5

        # Find recommended storage tier matching min_storage_gb
        storage_map = {"128GB": 128, "256GB": 256, "512GB": 512, "1TB": 1024}
        recommended_tier = next(
            (t for t in product.storage_tiers
             if storage_map.get(t.capacity, 0) >= max(min_storage_gb, 128)),
            product.storage_tiers[0]
        )

        ranked.append({
            "model_slug": product.model_slug,
            "display_name": product.display_name,
            "overall_score": round(normalized, 3),
            "score_breakdown": score_breakdown,
            "recommended_storage": recommended_tier.capacity,
            "recommended_price": recommended_tier.price_usd,
            "key_specs": {
                "chip": product.chip,
                "camera": f"{len(product.rear_cameras)}-camera system, {product.max_optical_zoom} optical zoom",
                "battery": f"{product.battery_hours_video}h video playback",
                "weight": f"{product.weight_grams}g",
                "display": f"{product.display_size}\" {product.display_type.split(',')[0]}",
            }
        })

    ranked.sort(key=lambda x: -x["overall_score"])

    return {
        "ranked": ranked,
        "top_pick": ranked[0] if ranked else None,
        "runner_up": ranked[1] if len(ranked) > 1 else None,
    }


def handle_compare_products(inp: dict) -> dict:
    slugs = inp.get("model_slugs", [])
    focus = inp.get("focus_aspects", ["camera", "battery", "value", "performance", "weight"])

    products = [catalog_store.get_by_slug(s) for s in slugs]
    products = [p for p in products if p is not None]

    if len(products) < 2:
        return {"error": "Need at least 2 valid model slugs to compare."}

    comparison = {}

    # Spec comparison
    spec_rows = {
        "Starting Price": lambda p: f"${p.starting_price}",
        "Chip": lambda p: p.chip,
        "Display": lambda p: f"{p.display_size}\" {p.display_type.split(',')[0]}",
        "Rear Cameras": lambda p: f"{len(p.rear_cameras)} cameras",
        "Max Optical Zoom": lambda p: p.max_optical_zoom,
        "Video": lambda p: p.video_max,
        "Battery (video)": lambda p: f"{p.battery_hours_video}h",
        "Weight": lambda p: f"{p.weight_grams}g",
        "Water Resistance": lambda p: p.water_resistance,
        "Connector": lambda p: p.connector,
        "Wi-Fi": lambda p: p.wifi,
    }

    for row_label, fn in spec_rows.items():
        comparison[row_label] = {p.model_slug: fn(p) for p in products}

    # Review score comparison for focused aspects
    review_comparison = {}
    for aspect in focus:
        review_comparison[aspect] = {}
        for p in products:
            evidence = _blended_score(p.model_slug, aspect)
            review_scores = catalog_store.get_review_scores(p.model_slug)
            vol = review_scores.get(aspect, {}).get("volume", 0)
            review_comparison[aspect][p.model_slug] = {
                "score": evidence["blended"],
                "review_volume": vol,
            }

    return {
        "models": [{"slug": p.model_slug, "name": p.display_name} for p in products],
        "spec_comparison": comparison,
        "aspect_scores": review_comparison,
    }


HANDLERS = {
    "extract_preferences": handle_extract_preferences,
    "search_catalog":      handle_search_catalog,
    "get_product_details": handle_get_product_details,
    "rank_iphones":        handle_rank_iphones,
    "compare_products":    handle_compare_products,
}


def dispatch(tool_name: str, tool_input: dict) -> dict:
    handler = HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return handler(tool_input)
    except Exception as e:
        return {"error": str(e)}
