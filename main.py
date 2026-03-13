import duckdb

con = duckdb.connect("AI_Engineering_case/jaffle_shop.duckdb", read_only=True)
for t in con.execute("SHOW TABLES").fetchall():
    name = t[0]
    print(f"\n=== {name} ===")
    for c in con.execute(f"DESCRIBE {name}").fetchall():
        print(f"  {c[0]}: {c[1]}")
    print(f"  Rows: {con.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]}")
    print("  Sample:")
    for r in con.execute(f"SELECT * FROM {name} LIMIT 3").fetchall():
        print(f"    {r}")
con.close()
