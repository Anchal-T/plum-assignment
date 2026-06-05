from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.claims import router as claims_router
from app.api.documents import router as documents_router
from app.config import settings
from app.rules.policy_loader import load_policy
from app.services.rule_engine import RuleEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = RuleEngine(load_policy(), settings)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Plum OPD Adjudicator", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "https://plum-assignment-99an.vercel.app",
            "https://plum-assignment-99an-anchal-ts-projects.vercel.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(claims_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
