from mcp.server.fastmcp import FastMCP
import db

mcp = FastMCP("jaffle-shop")

# ── Tools ────────────────────────────────────────────────────────────────

@mcp.tool()
def list_tables() -> list[str]:
    """List all tables in the Jaffle Shop database."""
    schema = db.get_schema()
    # Each line format: "table_name (N rows): col1 TYPE, col2 TYPE, ..."
    return [line.split("(")[0].strip() for line in schema.splitlines() if line.strip()]


@mcp.tool()
def describe_table(table_name: str) -> str:
    """Return columns and types for a specific table."""
    schema = db.get_schema()
    for line in schema.splitlines():
        if line.startswith(f"{table_name} ("):
            return line
    return f"Table '{table_name}' not found."


@mcp.tool()
def run_query(sql: str) -> str:
    """Execute a read-only SQL query and return results as a string."""
    result = db.run_query(sql)
    if isinstance(result, str):
        # run_query returns a string on error
        return f"ERROR: {result}"
    return result.to_string(index=False)


# ── Resources ──────────────────────────────────────────────────────────────────

@mcp.resource("jaffle://schema")
def schema_resource() -> str:
    """The full database schema as a string."""
    return db.get_schema()


@mcp.resource("jaffle://table/{table_name}")
def table_sample(table_name: str) -> str:
    """First 5 rows of a table as a preview."""
    result = db.run_query(f"SELECT * FROM {table_name} LIMIT 5")
    if isinstance(result, str):
        return f"ERROR: {result}"
    return result.to_string(index=False)


# ── Prompts ──────────────────────────────────────────────────────────────────

@mcp.prompt()
def analyze_question(question: str) -> str:
    """Generate a prompt that instructs the LLM to write SQL for a user question."""
    schema = db.get_schema()
    return f"""You are a data analyst for Jaffle Shop, a fictional sandwich chain.

Given this database schema:
{schema}

Write a DuckDB SQL query to answer the following question:
{question}

Respond as JSON with this exact structure:
{{"sql": "<your query>", "answer": "<one sentence description of what the query returns>", "chart": null}}"""


@mcp.prompt()
def explain_results(question: str, sql: str, results: str) -> str:
    """Generate a prompt that instructs the LLM to interpret query results in plain language."""
    return f"""A user asked: "{question}"

You ran this SQL query:
{sql}

The results were:
{results}

Write a clear, concise answer in plain language. Focus on insights, not just raw numbers."""



if __name__ == "__main__":
    mcp.run(transport="stdio")