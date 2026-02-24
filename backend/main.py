from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_catalog import router as catalog_router
from api.routes_chat import router as chat_router
from catalog.catalog_store import catalog_store
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up — loading catalog...")
    catalog_store.load(settings.CATALOG_PATH, settings.REVIEW_SCORES_PATH)
    print(f"Ready. {catalog_store.product_count} products loaded.")
    yield


app = FastAPI(title="Apple Store Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router)
app.include_router(chat_router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "catalog_loaded": catalog_store.product_count > 0,
        "product_count": catalog_store.product_count,
        "anthropic_key_set": bool(settings.ANTHROPIC_API_KEY),
    }
