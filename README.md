# Pyne

A chat-based AI assistant for querying the Jaffle Shop database using natural language. Ask business questions in plain English and get SQL queries, data tables, and charts in response - and the user is always absolutely right!

Built with Python, Dash, DuckDB, and using LLM APIs (Anthropic Claude or OpenAI GPT).

## Reflections and Design Choices

### Overall Design

I wanted to build a simple app with the backend handling queries to the DuckDB and LLM responses, along with a chat UI to display the LLM answer alongside SQL code and graphs/charts. 

Given that the quality of the responses would rely heavily on external LLMs, my main focus was to create consistency in the outputs - two identical questions should preferably give identical answers. I defined a clear system prompt and set the temperature to 0. The system prompt contains all the context (including dynamically loaded database schema) and requirements given to the LLM.

Outputs are constructed in a two-call process:
1. The user asks a questions -> the LLM returns SQL (first call to LLM)
2. The agent (backend) runs the SQL on the DuckDB and gets the query results
3. The agent sends the query results to the LLM (second call to LLM) and the LLM returns the final response
to the user

### Failure handling and Guardrails
If the SQL code is not returning data (pandas df), the error message (Exception) is sent to the LLM asking for a fix. If the SQL code still fails, an explanation of why the query might have failed is returned to the user. (Unfortunately?) the LLM is too smart to answer questions like: "Show me all employee salaries" and "What's the average shipping time?" that could produce SQL errors, so actual tests for this was hard to carry out.

Added early return when the SQL query contained specific keywords (DROP, DELETE, etc.). The database connection is also set to read-only as an additional safety layer.

### Evaluation
Pytest was used to test the structure and content of responses from the LLM: simple prompts asking about the data, where the answer can be easily verified. Tests also include a question about the weather to ensure that no SQL code or data is returned in the response in the case of out of scope questions.

### Improvements and Further Work
Some ideas that came to mind were:
- Implementing and using a self-hosted LLM to remove dependencies on external providers.
- Caching: Query results and LLM respones (time-aware, since the database would be expected to grow over time)
- Full report generation (with export) and more chart types

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
