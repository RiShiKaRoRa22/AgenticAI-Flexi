"""Tools the Executor agent can call. All are deterministic and read-only."""
import sqlite3, re
from db import DB_PATH, init_db
import os

def _con():
    if not os.path.exists(DB_PATH):
        init_db()
    return sqlite3.connect(DB_PATH)


def run_sql(query: str) -> dict:
    """Run a read-only SELECT query (max 50 rows)."""
    q = query.strip().rstrip(";")
    if not re.match(r"(?is)^\s*select\b", q) or re.search(
            r"(?i)\b(insert|update|delete|drop|alter|create|attach|pragma)\b", q):
        return {"error": "Only single SELECT statements are allowed."}
    try:
        cur = _con().execute(q)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchmany(50)
        return {"columns": cols, "rows": rows}
    except Exception as e:
        return {"error": str(e)}


def monthly_summary(month: str) -> dict:
    """Total spend per category for a month (YYYY-MM) with budget comparison."""
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        return {"error": "month must look like 2026-09"}
    rows = _con().execute("""
        SELECT e.category, ROUND(SUM(e.amount),2), b.monthly_limit
        FROM expenses e JOIN budgets b ON e.category=b.category
        WHERE substr(e.date,1,7)=? GROUP BY e.category ORDER BY 2 DESC""", (month,)).fetchall()
    out = [{"category": c, "spent": s, "budget": b, "remaining": round(b - s, 2)}
           for c, s, b in rows]
    return {"month": month, "total": round(sum(r["spent"] for r in out), 2), "categories": out}


def detect_overspend(month: str) -> dict:
    """Categories where spend exceeded the monthly budget."""
    summ = monthly_summary(month)
    if "error" in summ:
        return summ
    over = [{**c, "over_by": round(-c["remaining"], 2)}
            for c in summ["categories"] if c["remaining"] < 0]
    return {"month": month, "overspent_categories": over}


TOOL_FUNCS = {"run_sql": run_sql, "monthly_summary": monthly_summary,
              "detect_overspend": detect_overspend}

TOOL_SCHEMAS = [
    {"name": "run_sql",
     "description": "Run a read-only SQLite SELECT. Tables: expenses(id,date 'YYYY-MM-DD',category,description,amount), budgets(category,monthly_limit). Use for custom questions (top N, date ranges, averages).",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "monthly_summary",
     "description": "Spend per category vs budget for one month.",
     "input_schema": {"type": "object", "properties": {"month": {"type": "string", "description": "YYYY-MM"}}, "required": ["month"]}},
    {"name": "detect_overspend",
     "description": "List categories that exceeded their monthly budget.",
     "input_schema": {"type": "object", "properties": {"month": {"type": "string", "description": "YYYY-MM"}}, "required": ["month"]}},
]
