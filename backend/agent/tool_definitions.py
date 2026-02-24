TOOLS = [
    {
        "name": "extract_preferences",
        "description": "Extract a structured PreferenceVector from the conversation so far. "
                       "Call this first whenever the user describes their needs, budget, or usage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "budget_max": {"type": "integer", "description": "Maximum budget in USD, or null if unstated"},
                "priorities": {
                    "type": "object",
                    "description": "Importance weights 0-1 for each dimension the user cares about",
                    "properties": {
                        "camera":      {"type": "number"},
                        "battery":     {"type": "number"},
                        "performance": {"type": "number"},
                        "display":     {"type": "number"},
                        "weight":      {"type": "number"},
                        "value":       {"type": "number"}
                    }
                },
                "usage": {
                    "type": "object",
                    "properties": {
                        "photo_video": {"type": "string", "enum": ["none", "low", "medium", "high"]},
                        "gaming":      {"type": "string", "enum": ["none", "low", "medium", "high"]},
                        "work":        {"type": "string", "enum": ["none", "low", "medium", "high"]},
                        "social":      {"type": "string", "enum": ["none", "low", "medium", "high"]}
                    }
                },
                "constraints": {
                    "type": "object",
                    "properties": {
                        "min_storage_gb": {"type": "integer"},
                        "must_have": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "e.g. ['telephoto', 'ProMotion', 'USB3']"
                        },
                        "size_preference": {"type": "string", "enum": ["compact", "any", "large"]}
                    }
                },
                "apps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Apps the user mentioned using"
                }
            },
            "required": ["priorities"]
        }
    },
    {
        "name": "search_catalog",
        "description": "Search and filter the iPhone catalog. Returns matching products with key specs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":     {"type": "string",  "description": "Natural language query, e.g. 'best camera phone'"},
                "series":    {"type": "string",  "description": "Filter by: 'iPhone 17 Pro', 'iPhone 17', 'iPhone 17 Air'"},
                "max_price": {"type": "integer", "description": "Maximum starting price in USD"},
                "tier":      {"type": "string",  "enum": ["pro", "standard"], "description": "Filter by tier"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_product_details",
        "description": "Get full specifications and review sentiment scores for a specific iPhone model.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_slug": {"type": "string", "description": "e.g. 'iphone-17-pro-max', 'iphone-17-air'"}
            },
            "required": ["model_slug"]
        }
    },
    {
        "name": "rank_iphones",
        "description": "Rank iPhones using a PreferenceVector. Blends spec scores (60%) with review sentiment (40%). "
                       "Always call this after extract_preferences to get evidence-based rankings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "preferences": {
                    "type": "object",
                    "description": "The PreferenceVector from extract_preferences"
                },
                "candidate_slugs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: restrict to specific models. Leave empty to rank all."
                }
            },
            "required": ["preferences"]
        }
    },
    {
        "name": "compare_products",
        "description": "Side-by-side spec + review comparison of 2-3 iPhone models.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_slugs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 3
                },
                "focus_aspects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Aspects to highlight, e.g. ['camera', 'battery', 'value']"
                }
            },
            "required": ["model_slugs"]
        }
    }
]
