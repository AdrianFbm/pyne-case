from __future__ import annotations

import re

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
    data: pd.DataFrame | None = None

if settings.llm_provider == "anthropic":
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
else:
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)

from pathlib import Path

_prompt_template = Path(__file__).with_name("system_prompt.md").read_text()
SYSTEM_PROMPT = _prompt_template.format(schema=get_schema())


def _llm_response_to_json(response: LLMResponse) -> str:
    """Serialize an LLMResponse for inclusion in chat messages."""
    return response.model_dump_json()


def ask(question: str, chat_history: list[dict] | None = None) -> AgentResponse:
    """Send a question to the LLM, execute any SQL, and return the final response."""
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": question})

    response = _call_llm(messages)

    # If no SQL, it's a clarification — return as-is
    if not response.sql:
        return AgentResponse(
            answer=response.answer,
            chart=response.chart,
        )

    # Execute the SQL
    result = run_query(response.sql)

    # If SQL failed, retry once with the error
    if isinstance(result, str):
        messages.append({"role": "assistant", "content": _llm_response_to_json(response)})
        messages.append({
            "role": "user",
            "content": f"That query failed with: {result}\nPlease fix the SQL and try again.",
        })
        response = _call_llm(messages)
        if not response.sql:
            return AgentResponse(
                answer=response.answer,
                chart=response.chart,
            )
        result = run_query(response.sql)
        if isinstance(result, str):
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
    final = _call_llm(messages)
    return AgentResponse(
        sql=response.sql,
        answer=final.answer,
        chart=final.chart,
        data=result,
    )


def _call_llm(messages: list[dict]) -> LLMResponse:
    """Call the configured LLM provider and parse the JSON response."""
    if settings.llm_provider == "anthropic":
        resp = client.messages.create(
            model=settings.llm_model,
            max_tokens=1024,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        text = resp.content[0].text.strip()
    else:
        openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]
        resp = client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=1024,
            temperature=0,
            messages=openai_messages,
        )
        text = resp.choices[0].message.content.strip()

    # Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)

    try:
        return LLMResponse.model_validate_json(text)
    except Exception:
        return LLMResponse(answer=text)
