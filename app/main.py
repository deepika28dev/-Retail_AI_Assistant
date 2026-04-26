from fastapi import FastAPI

from app.api.routes.chat import router as chat_router


def create_app() -> FastAPI:
    fastapi_app = FastAPI(
        title="Retail AI Assistant",
        version="1.0.0",
        description="FastAPI implementation for the Retail AI Assistant assignment.",
    )
    fastapi_app.include_router(chat_router)
    return fastapi_app


app = create_app()
