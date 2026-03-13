import json
import anthropic
from db import get_schema, run_query

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = f"""You are a data analyst for Jaffle Shop, a fictional sandwich chain.
You answer business questions by writing SQL against a DuckDB database, then explaining the results in plain language.

DATABASE SCHEMA:
{get_schema()}

INSTRUCTIONS:
- Write a single DuckDB-compatible SQL query to answer the user's question.
- After seeing the results, provide a clear narrative answer a non-technical person can understand.
- When a chart would help (trends, comparisons, distributions), include a chart spec.
- If the question is ambiguous, ask for clarification instead of guessing.

RESPONSE FORMAT — always respond with valid JSON and nothing else:
{{
  "sql": "SELECT ...",
  "answer": "Markdown narrative explaining the results",
  "chart": null OR {{"type": "bar|line|pie", "x": "column_name", "y": "column_name", "title": "Chart Title"}}
}}

If you need clarification instead of running a query, respond with:
{{
  "sql": null,
  "answer": "Your clarifying question here",
  "chart": null
}}"""


def ask(question: str, chat_history: list[dict] | None = None) -> dict:
    """Send a question to Claude, execute any SQL, and return the final response.

    Returns dict with keys: sql, answer, chart, data (DataFrame or None).
    """
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": question})

    response = _call_claude(messages)

    # If no SQL, it's a clarification — return as-is
    if not response.get("sql"):
        return {**response, "data": None}

    # Execute the SQL
    result = run_query(response["sql"])

    # If SQL failed, retry once with the error
    if isinstance(result, str):
        messages.append({"role": "assistant", "content": json.dumps(response)})
        messages.append({
            "role": "user",
            "content": f"That query failed with: {result}\nPlease fix the SQL and try again.",
        })
        response = _call_claude(messages)
        if not response.get("sql"):
            return {**response, "data": None}
        result = run_query(response["sql"])
        if isinstance(result, str):
            return {"sql": response["sql"], "answer": f"Sorry, I couldn't run that query: {result}", "chart": None, "data": None}

    # Success — ask Claude to interpret the results
    messages.append({"role": "assistant", "content": json.dumps(response)})
    messages.append({
        "role": "user",
        "content": f"Query results (first 50 rows):\n{result.head(50).to_string(index=False)}\n\nNow provide your final JSON response with the narrative answer and optional chart spec.",
    })
    final = _call_claude(messages)
    final["sql"] = response["sql"]
    final["data"] = result
    return final


def _call_claude(messages: list[dict]) -> dict:
    """Call the Claude API and parse the JSON response."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    text = resp.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)
