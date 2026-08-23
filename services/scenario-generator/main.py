from contextlib import asynccontextmanager

from fastapi import FastAPI

import models
from database import Base, engine
from routers.scenarios import router as scenarios_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Scenario Generator", version="0.1.0", lifespan=lifespan)
    app.include_router(scenarios_router)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "service": "scenario-generator"}

    return app


app = create_app()
