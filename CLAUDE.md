# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Pyne / AIoli** is a chat-based AI assistant for querying the Jaffle Shop (fictional sandwich chain) DuckDB database. Users ask natural language questions; the agent generates SQL, executes it, and returns an interpreted answer with optional Plotly charts.

## Commands

**Run the app:**
```bash
python run.py
```

**Run tests:**
```bash
pytest tests/
```

**Run a single test:**
```bash
pytest tests/test_eval.py::test_customer_count
```

**Run the lightweight eval script (not pytest):**
```bash
python eval/test_queries.py
```

**Dependencies** are managed with `pyproject.toml`. Python 3.12 required (see `.python-version`).

## Architecture

### Two-call LLM pattern (`agent.py`)
The core flow in `ask()`:
1. User question → LLM returns JSON with `sql`, `answer`, `chart` fields
2. Execute the SQL via `db.py`
3. If SQL fails: retry once (sending the error back to the LLM), then ask LLM to explain the error in plain language
4. If SQL succeeds: send results back to LLM for a final narrative interpretation
5. Return `AgentResponse` (includes the DataFrame as `sql_data`)

### LLM provider switching (`settings.py` + `agent.py`)
- Configured via `LLM_PROVIDER` env var (`anthropic` or `openai`)
- Defaults: `claude-sonnet-4-20250514` (Anthropic) or `gpt-4o` (OpenAI)
- Tests use Haiku 4.5 for speed — see `test_eval.py`

### UI structure (`app.py`)
Dash app with two panels:
- **Left sidebar**: Collapsible schema browser + standalone SQL editor with "Run" button
- **Main area**: Chat interface with message history, loading animation, copy-SQL-to-editor button

State is managed via `dcc.Store` components: `chat-history` (raw LLM history), `display-messages` (rendered HTML), `pending-question`, `latest-chat-sql`.

### Database (`db.py`)
- DuckDB file at `AI_Engineering_case/jaffle_shop.duckdb`
- Read-only connection; blocked keywords: DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE, REPLACE
- `get_schema()` queries column metadata and formats it for the system prompt
- `run_query()` returns a pandas DataFrame on success, or an error string on failure

### System prompt (`system_prompt.md`)
Template populated with `{schema}` at `LLMClient` instantiation. Instructs the LLM to respond strictly as JSON with `sql`, `answer`, and `chart` fields. The `chart` field supports `bar`, `line`, `pie` types.

## Testing Approach

Tests in `tests/test_eval.py` validate DataFrame contents (row counts, column values) rather than narrative text, making them deterministic. The `ask()` function is called end-to-end — these are integration tests hitting the real LLM and database.
