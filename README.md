# Student Expense Analyst Agent
Multi-agent (Planner -> Executor -> Reviewer) assistant that answers spending questions using SQLite tools.

## Run
```
pip install -r requirements.txt
cp .env.example .env        # add GROQ_API_KEY
python db.py                # create data
pytest tests -v             # tool tests (no API key)
python main.py "Which categories did I overspend in September 2026?"
python tests/run_eval.py    # end-to-end evidence -> evidence.md
streamlit run app.py        # web UI
```
