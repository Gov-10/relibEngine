from fastapi import FastAPI

import models
from routers.analysis import router as analysis_router


def create_app() -> FastAPI:
    app = FastAPI(title="Analyzer & Reliability Service", version="0.1.0")
    app.include_router(analysis_router)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "service": "analyzer"}

    return app


app = create_app()
