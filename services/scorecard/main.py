from contextlib import asynccontextmanager

from fastapi import FastAPI

import store
from routers.scorecards import router as scorecards_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Scorecard Service", version="0.1.0", lifespan=lifespan)
    app.include_router(scorecards_router)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "service": "scorecard"}

    return app


app = create_app()
