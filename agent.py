from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

import pandas as pd
from pydantic import BaseModel

from db import get_schema, run_query
from settings import settings


class LLMResponse(BaseModel):
    sql: str | None = None
    answer: str = ""
    chart: dict | None = None


class AgentResponse(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    sql: str | None = None
    answer: str = ""
    chart: dict | None = None
    sql_data: pd.DataFrame | None = None


class LLMClient:
    def __init__(self):
        # Initializing the system prompt and adding the current schema
        prompt_template = Path(__file__).with_name("system_prompt.md").read_text()
        self._system_prompt = prompt_template.format(schema=get_schema())

        # Establish connection to the LLM provider
        if settings.llm_provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        else:
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.openai_api_key)

    # Generic method to call the LLM
    def _call_llm(self, messages: list[dict]) -> LLMResponse:
        """Call the LLM and parse the JSON response."""
        if settings.llm_provider == "anthropic":
            resp = self._client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                system=self._system_prompt,
                messages=messages,
            )
            text = resp.content[0].text.strip()
        else:
            openai_messages = [{"role": "system", "content": self._system_prompt}, *messages]
            resp = self._client.chat.completions.create(
                model=settings.llm_model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                messages=openai_messages,
            )
            text = resp.choices[0].message.content.strip()

        # Strip markdown code fences if present
        fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1)

        try:
            return LLMResponse.model_validate_json(text)
        except Exception as e:
            logger.warning("Failed to parse LLM response: %s", e)
            return LLMResponse(answer=text)


_llm = LLMClient()


def _llm_response_to_json(response: LLMResponse) -> str:
    """Serialize an LLMResponse for inclusion in chat messages."""
    return response.model_dump_json()


def _retry_failed_sql(
    messages: list[dict], response: LLMResponse, error: str
) -> tuple[LLMResponse, pd.DataFrame | str]:
    """Re-ask the LLM to fix a failed SQL query and retry execution once."""
    messages.append({"role": "assistant", "content": _llm_response_to_json(response)})
    messages.append({
        "role": "user",
        "content": f"That query failed with: {error}\nPlease fix the SQL and try again.",
    })
    response = _llm._call_llm(messages)
    if not response.sql:
        return response, error
    return response, run_query(response.sql)


def ask(question: str, chat_history: list[dict] | None = None) -> AgentResponse:
    """Send a question to the LLM, execute any SQL, and return the final response."""
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": question})

    response = _llm._call_llm(messages)

    # If no SQL, it's a clarification — return as-is
    if not response.sql:
        return AgentResponse(
            answer=response.answer,
            chart=response.chart,
            sql_data=None,
        )

    # Execute the SQL - connection is handled inside run_query
    result = run_query(response.sql)

    if isinstance(result, str):
        response, result = _retry_failed_sql(messages, response, result)
        if isinstance(result, str):
            # If the SQL still fails, return the error message and the failed SQL
            return AgentResponse(
                sql=response.sql,
                answer=f"Sorry, I couldn't run that query: {result}",
            )

    # Success — ask the LLM to interpret the results
    messages.append({"role": "assistant", "content": _llm_response_to_json(response)})
    messages.append({
        "role": "user",
        "content": f"Query results (first 50 rows):\n{result.head(50).to_string(index=False)}\n\nNow provide your final JSON response with the narrative answer and optional chart spec.",
    })
    final = _llm._call_llm(messages)
    return AgentResponse(
        sql=response.sql,
        answer=final.answer,
        chart=final.chart,
        sql_data=result,
    )


