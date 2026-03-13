# Pyne

A chat-based AI assistant for querying the Jaffle Shop database using natural language. Ask business questions in plain English and get SQL queries, data tables, and charts in response.

Built with Dash, DuckDB, and LLM APIs (Anthropic Claude or OpenAI GPT).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Browser                          │
│  ┌───────────┐  ┌────────────────────────────────────┐  │
│  │  Sidebar  │  │           Chat Interface           │  │
│  │  (Schema) │  │  ┌─────────┐  ┌────────────────┐   │  │
│  │           │  │  │ User msg│  │ Assistant msg  │   │  │
│  │ customers │  │  └─────────┘  │ + SQL + Table  │   │  │
│  │ orders    │  │               │ + Chart        │   │  │
│  │ products  │  │               └────────────────┘   │  │
│  │ order_    │  │  ┌──────────────────┐ ┌──────┐     │  │
│  │   items   │  │  │  Text input      │ │ Send │     │  │
│  │           │  │  └──────────────────┘ └──────┘     │  │
│  └───────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │     app.py       │
                 │  (Dash server)   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    agent.py      │
                 │ (LLM orchestr.)  │
                 └───┬──────────┬───┘
                     │          │
                     ▼          ▼
            ┌────────────┐  ┌──────────────────┐
            │ settings.py│  │     db.py        │
            │ (config)   │  │ (DuckDB queries) │
            └─────┬──────┘  └────────┬─────────┘
                  │                  │
                  ▼                  ▼
           ┌─────────────┐  ┌──────────────┐
           │    .env     │  │ jaffle_shop  │
           │  API keys   │  │   .duckdb    │
           └──────┬──────┘  └──────────────┘
                  │
                  ▼
        ┌───────────────────┐
        │   LLM Provider    │
        │  ┌─────────────┐  │
        │  │  Anthropic  │  │
        │  │  (Claude)   │  │
        │  ├─────────────┤  │
        │  │  OpenAI     │  │
        │  │  (GPT)      │  │
        │  └─────────────┘  │
        └───────────────────┘
```

## How it works

1. User asks a question in the chat
2. `agent.py` sends the question + database schema to the configured LLM
3. The LLM responds with a SQL query and explanation (JSON)
4. `db.py` executes the SQL against the DuckDB database
5. Results are sent back to the LLM for a narrative summary
6. `app.py` renders the answer, data table, and optional chart

## Setup

```bash
# Install dependencies
uv sync

# Configure API keys in .env
ANTHROPIC_API_KEY="sk-ant-..."
# or
OPENAI_API_KEY="sk-proj-..."

# Optionally set provider and model
LLM_PROVIDER="anthropic"   # auto-detected from available keys if omitted
LLM_MODEL="claude-sonnet-4-20250514"

# Run
python run.py
```

Open http://127.0.0.1:8050 in your browser.

## Project structure

```
├── app.py          # Dash UI (layout, callbacks, styling)
├── agent.py        # LLM orchestration (prompt, retry, response parsing)
├── db.py           # DuckDB connection and query execution
├── settings.py     # Pydantic BaseSettings configuration
├── run.py          # Entry point
├── main.py         # DB inspection utility
└── .env            # API keys (not committed)
```
