import duckdb
import pandas as pd

DB_PATH = "AI_Engineering_case/jaffle_shop.duckdb"


def get_schema() -> str:
    """Return a text description of all tables and columns for the LLM prompt."""
    con = duckdb.connect(DB_PATH, read_only=True)
    lines = []
    for (table_name,) in con.execute("SHOW TABLES").fetchall():
        cols = con.execute(f"DESCRIBE {table_name}").fetchall()
        row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        col_defs = ", ".join(f"{c[0]} {c[1]}" for c in cols)
        lines.append(f"{table_name} ({row_count} rows): {col_defs}")
    con.close()
    return "\n".join(lines)


def run_query(sql: str) -> pd.DataFrame | str:
    """Execute SQL and return a DataFrame on success or an error string on failure."""
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        result = con.execute(sql).fetchdf()
        return result
    except Exception as e:
        return f"SQL Error: {e}"
    finally:
        con.close()
