from fastapi.testclient import TestClient

from app.api.routes import chat as chat_route
from app.main import app
from app.schemas.domain import AgentAnswer


class FakeAgent:
    def run(self, message):
        return AgentAnswer(answer=f"Received: {message}", tool_trace=[])


class FakeContainer:
    agent = FakeAgent()


class FailingAgent:
    def run(self, message):
        raise RuntimeError("HUGGINGFACE_API_KEY is missing.")


class FailingContainer:
    agent = FailingAgent()


def test_chat_endpoint_returns_agent_answer(monkeypatch):
    monkeypatch.setattr(chat_route, "get_container", lambda: FakeContainer())
    client = TestClient(app)

    response = client.post("/chat", json={"message": "Find sale dresses in size 8"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Received: Find sale dresses in size 8",
        "tool_trace": [],
    }


def test_chat_endpoint_returns_fallback_json(monkeypatch):
    monkeypatch.setattr(chat_route, "get_container", lambda: FailingContainer())
    client = TestClient(app)

    response = client.post("/chat", json={"message": "Find sale dresses in size 8"})

    assert response.status_code == 200
    body = response.json()
    assert "Hugging Face LLM provider is unavailable" in body["answer"]
    assert body["tool_trace"][0]["tool_name"] == "fallback"
    assert body["tool_trace"][0]["result"]["provider"] == "huggingface"
