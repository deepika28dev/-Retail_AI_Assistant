from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.agent.prompts import SYSTEM_PROMPT
from app.config import Settings
from app.schemas.domain import AgentAnswer
from app.tools.registry import ToolRegistry


class RetailAgent:
    def __init__(self, settings: Settings, tool_registry: ToolRegistry):
        self.settings = settings
        self.tool_registry = tool_registry

    def run(self, user_message: str) -> AgentAnswer:
        client, model = self._create_client()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        tool_trace: list[dict[str, Any]] = []

        for _ in range(6):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=self.tool_registry.openai_tools(),
                tool_choice="auto",
                temperature=0,
            )
            assistant_message = response.choices[0].message

            if not assistant_message.tool_calls:
                return AgentAnswer(
                    answer=assistant_message.content or "I could not generate a response.",
                    tool_trace=tool_trace,
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in assistant_message.tool_calls
                    ],
                }
            )

            for tool_call in assistant_message.tool_calls:
                result = self.tool_registry.execute(
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                )
                tool_trace.append(
                    {
                        "tool_name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments or "{}"),
                        "result": result,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

        raise RuntimeError("The agent reached the tool-call limit before finishing the answer.")

    def _create_client(self) -> tuple[OpenAI, str]:
        if not self.settings.huggingface_api_key:
            raise RuntimeError(
                "HUGGINGFACE_API_KEY is missing. Set it in your environment or .env file before running the agent."
            )
        return (
            OpenAI(
                api_key=self.settings.huggingface_api_key,
                base_url=self.settings.huggingface_base_url,
            ),
            self.settings.huggingface_model,
        )
