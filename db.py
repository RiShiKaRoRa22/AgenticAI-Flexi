"""Creates and seeds a deterministic SQLite database of student expenses (INR)."""
import sqlite3, random, datetime, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")

CATEGORY_RANGES = {            # (min, max) per transaction
    "Food": (60, 450),
    "Transport": (30, 300),
    "Entertainment": (150, 1200),
    "Shopping": (300, 2500),
    "Education": (200, 1800),
}
BUDGETS = {"Food": 6000, "Transport": 3000, "Entertainment": 2500,
           "Shopping": 4000, "Education": 3500}   # monthly limits


def init_db(path: str = DB_PATH, seed: int = 42) -> str:
    if os.path.exists(path):
        os.remove(path)
    random.seed(seed)
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE expenses(
        id INTEGER PRIMARY KEY, date TEXT, category TEXT,
        description TEXT, amount REAL)""")
    con.execute("CREATE TABLE budgets(category TEXT PRIMARY KEY, monthly_limit REAL)")
    con.executemany("INSERT INTO budgets VALUES (?,?)", BUDGETS.items())

    start = datetime.date(2026, 8, 1)
    rows = []
    for d in range(61):                       # Aug 1 - Sep 30, 2026
        day = start + datetime.timedelta(days=d)
        for _ in range(random.randint(1, 3)):
            cat = random.choice(list(CATEGORY_RANGES))
            lo, hi = CATEGORY_RANGES[cat]
            amt = round(random.uniform(lo, hi), 2)
            rows.append((day.isoformat(), cat, f"{cat} spend", amt))
    con.executemany(
        "INSERT INTO expenses(date,category,description,amount) VALUES (?,?,?,?)", rows)
    con.commit()
    con.close()
    return path


if __name__ == "__main__":
    print("Database created at", init_db())
