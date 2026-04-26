from __future__ import annotations

from fastapi import APIRouter, HTTPException
from openai import APIConnectionError, APIStatusError, RateLimitError

from app.container import get_container
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = get_container().agent.run(request.message)
        return ChatResponse(answer=result.answer, tool_trace=result.tool_trace)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except RateLimitError as error:
        return _fallback_response("Hugging Face quota or rate limit was reached.", error)
    except APIConnectionError as error:
        return _fallback_response("Could not connect to the Hugging Face API.", error)
    except APIStatusError as error:
        return _fallback_response(
            f"Hugging Face returned an error: {error.status_code}.",
            error,
            provider_detail=_provider_error_detail(error),
        )
    except RuntimeError as error:
        return _fallback_response(str(error), error)


def _fallback_response(message: str, error: Exception, provider_detail: str | None = None) -> ChatResponse:
    detail = provider_detail or str(error)
    return ChatResponse(
        answer=(
            "I cannot complete this chat request right now because the Hugging Face LLM provider is unavailable. "
            f"{message}"
        ),
        tool_trace=[
            {
                "tool_name": "fallback",
                "arguments": {},
                "result": {
                    "provider": "huggingface",
                    "error_type": error.__class__.__name__,
                    "detail": detail,
                },
            }
        ],
    )


def _provider_error_detail(error: APIStatusError) -> str:
    try:
        provider_detail = error.response.json()
    except ValueError:
        provider_detail = error.response.text

    if not provider_detail:
        return error.message

    return str(provider_detail)
