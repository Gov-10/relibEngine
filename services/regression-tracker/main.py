from contextlib import asynccontextmanager

from fastapi import FastAPI

import store
from routers.regressions import router as regressions_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Regression Tracker", version="0.1.0", lifespan=lifespan)
    app.include_router(regressions_router)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "service": "regression-tracker"}

    return app


app = create_app()
