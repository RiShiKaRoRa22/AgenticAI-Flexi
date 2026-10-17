"""Deterministic tests - no API key needed. Ground truth computed independently in SQL/Python."""
import sqlite3, pytest
from db import init_db, DB_PATH, BUDGETS
import tools

@pytest.fixture(scope="module", autouse=True)
def _db():
    init_db()

def truth(month, cat=None):
    con = sqlite3.connect(DB_PATH)
    q = "SELECT category, SUM(amount) FROM expenses WHERE substr(date,1,7)=? GROUP BY category"
    return {c: s for c, s in con.execute(q, (month,))}

def test_monthly_summary_matches_ground_truth():
    res = tools.monthly_summary("2026-09")
    t = truth("2026-09")
    for c in res["categories"]:
        assert c["spent"] == pytest.approx(t[c["category"]], abs=0.01)

def test_overspend_logic():
    res = tools.detect_overspend("2026-09")
    t = truth("2026-09")
    expected = {c for c, s in t.items() if s > BUDGETS[c]}
    assert {c["category"] for c in res["overspent_categories"]} == expected

def test_sql_tool_rejects_writes():
    assert "error" in tools.run_sql("DROP TABLE expenses")
    assert "error" in tools.run_sql("DELETE FROM expenses")
    assert "error" in tools.run_sql("SELECT 1; DROP TABLE expenses")

def test_sql_tool_valid_select():
    res = tools.run_sql("SELECT COUNT(*) FROM expenses")
    assert res["rows"][0][0] > 0

def test_bad_month_format():
    assert "error" in tools.monthly_summary("Sept 2026")
