from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import sqlglot
import os
import requests
from time import time

app = FastAPI()

# --- Your connection string ---
DATABASE_URL = "postgresql://chatbot_readonly.occiztgbyxtslbuhtavb:Churchgate@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"
# --------------------------------

TABS_DIR = os.path.join(os.path.dirname(__file__), "tabs")

# --- NEW: simple in-memory cache ---
_query_cache = {}
CACHE_TTL_SECONDS = 300  # 5 minutes
# ------------------------------------


def get_connection():
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SET search_path TO public, engineering;")
    cur.close()
    return conn


class SQLRequest(BaseModel):
    query: str


@app.get("/schema")
def get_schema(table_name: str = None):
    """Shows what tables and columns exist. Optionally filter to one table."""
    conn = get_connection()
    cur = conn.cursor()
    if table_name:
        cur.execute("""
            select table_schema, table_name, column_name, data_type
            from information_schema.columns
            where table_schema in ('public', 'engineering') and table_name = %s
            order by ordinal_position;
        """, (table_name,))
    else:
        cur.execute("""
            select table_schema, table_name, column_name, data_type
            from information_schema.columns
            where table_schema in ('public', 'engineering')
            order by table_schema, table_name, ordinal_position;
        """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    schema = {}
    for schema_name, table, column, dtype in rows:
        key = f"{schema_name}.{table}" if schema_name != "public" else table
        schema.setdefault(key, []).append(f"{column} ({dtype})")
    return schema


@app.get("/tab-reference")
def get_tab_reference(tab_name: str):
    """Returns the markdown reference file for a given tab."""
    valid_tabs = {"revenue", "product_usage", "customer_support", "engineering", "user360", "complex_queries"}
    if tab_name not in valid_tabs:
        raise HTTPException(status_code=400, detail=f"Unknown tab '{tab_name}'. Valid tabs: {', '.join(valid_tabs)}")

    file_path = os.path.join(TABS_DIR, f"{tab_name}.md")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Reference file for '{tab_name}' not found.")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"tab": tab_name, "content": content}


@app.post("/execute-sql")
def execute_sql(req: SQLRequest):
    """Safely runs a SELECT query and returns the results."""
    query = req.query.strip()

    # --- NEW: check cache first, before any validation/execution ---
    now = time()
    if query in _query_cache:
        cached_result, cached_time = _query_cache[query]
        if now - cached_time < CACHE_TTL_SECONDS:
            print(f"Cache hit: {query}")
            return cached_result
    # ----------------------------------------------------------------

    # 1. Make sure it's a SELECT/WITH query only, nothing else
    try:
        parsed = sqlglot.parse(query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not understand this SQL: {e}")

    if len(parsed) != 1:
        raise HTTPException(status_code=400, detail="Only one query at a time is allowed.")

    statement_type = parsed[0].key.lower()
    if statement_type not in ("select", "with"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")

    # 2. Add a safety limit if there isn't one already
    if "limit" not in query.lower():
        query = query.rstrip(";") + " LIMIT 100;"

    print(f"Running SQL: {query}")   # <-- shows the actual query in your terminal

    # 3. Run it
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SET statement_timeout = 5000;")
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query failed: {e}")

    results = [dict(zip(columns, row)) for row in rows]
    response = {"results": results}

    # --- NEW: store in cache before returning ---
    _query_cache[req.query.strip()] = (response, now)
    # ---------------------------------------------

    return response