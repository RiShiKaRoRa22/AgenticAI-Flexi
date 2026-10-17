import streamlit as st
from db import init_db
from agents import run

st.set_page_config(page_title="Expense Agent", page_icon="💸")
st.title("💸 Student Expense Analyst Agent")
st.caption("Planner → Executor (SQL/budget tools) → Reviewer. Data: Aug–Sep 2026, INR.")
init_db()
q = st.text_input("Ask about your spending",
                  "Which categories did I overspend in September 2026?")
if st.button("Ask") and q:
    with st.spinner("Agents working..."):
        res = run(q)
    st.subheader("Answer"); st.write(res["answer"])
    st.subheader("Reviewer verdict"); st.json(res["review"])
    with st.expander("Planner's plan"): st.write(res["plan"])
    with st.expander("Tool calls and raw outputs"): st.json(res["trace"])
