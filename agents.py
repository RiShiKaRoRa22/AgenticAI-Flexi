"""Three cooperating agents: Planner -> Executor (tool user) -> Reviewer (verifier).
Uses Groq's free, OpenAI-compatible API."""
import os, json
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOL_FUNCS, TOOL_SCHEMAS

load_dotenv()
client = OpenAI(api_key=os.getenv("GROQ_API_KEY", "missing"),
                base_url="https://api.groq.com/openai/v1")
MODEL = os.getenv("MODEL", "openai/gpt-oss-20b")

# tools.py stores schemas in a neutral format; convert to OpenAI/Groq format
OPENAI_TOOLS = [{"type": "function",
                 "function": {"name": t["name"], "description": t["description"],
                              "parameters": t["input_schema"]}} for t in TOOL_SCHEMAS]

PLANNER_SYS = """You are the Planner agent of a student expense assistant.
Data covers 2026-08-01 to 2026-09-30, amounts in INR. Tools available to the Executor:
run_sql, monthly_summary, detect_overspend. Given the user question, write a short numbered
plan (max 4 steps) naming which tool to use for each step. Do not answer the question."""

EXECUTOR_SYS = """You are the Executor agent. Follow the plan, call tools to get real numbers,
and never guess or compute figures from memory. Answer concisely in INR with exact figures from
tool results, then add one short, practical saving tip if the question is about overspending.
If the user asks you to modify or delete data, refuse: you only have read-only tools."""

REVIEWER_SYS = """You are the Reviewer agent. You get a question, the tool calls with their raw
results, and a draft answer. Check that every number in the answer appears in the tool results
(or is a correct simple derivation) and that the question was actually answered.
Reply ONLY with JSON: {"verdict": "PASS" or "FAIL", "issues": "<short text>"}."""


def _chat(system, user, **kw):
    r = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], **kw)
    return (r.choices[0].message.content or "").strip()


def planner(question: str) -> str:
    return _chat(PLANNER_SYS, question, max_tokens=400)


def executor(question: str, plan: str, trace: list, feedback: str = "") -> str:
    prompt = f"Question: {question}\n\nPlan:\n{plan}"
    if feedback:
        prompt += f"\n\nReviewer feedback on your previous attempt (fix this): {feedback}"
    messages = [{"role": "system", "content": EXECUTOR_SYS},
                {"role": "user", "content": prompt}]
    for _ in range(6):                                   # safety cap on tool loops
        r = client.chat.completions.create(model=MODEL, temperature=0, max_tokens=1000,
                                           messages=messages, tools=OPENAI_TOOLS)
        msg = r.choices[0].message
        if not msg.tool_calls:
            return (msg.content or "").strip()
        messages.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": [{"id": tc.id, "type": "function",
                                         "function": {"name": tc.function.name,
                                                      "arguments": tc.function.arguments}}
                                        for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
                out = TOOL_FUNCS[tc.function.name](**args)
            except Exception as e:
                args, out = {}, {"error": str(e)}
            trace.append({"tool": tc.function.name, "input": args, "output": out})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(out)})
    return "Stopped: too many tool steps."


def reviewer(question: str, answer: str, trace: list) -> dict:
    payload = json.dumps({"question": question, "tool_calls": trace, "draft_answer": answer})
    txt = _chat(REVIEWER_SYS, payload, max_tokens=300)
    txt = txt.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"verdict": "FAIL", "issues": "Reviewer returned invalid JSON"}


def run(question: str) -> dict:
    trace: list = []
    plan = planner(question)
    answer = executor(question, plan, trace)
    review = reviewer(question, answer, trace)
    retried = False
    if review.get("verdict") == "FAIL":                  # one self-correction round
        retried = True
        answer = executor(question, plan, trace, feedback=review.get("issues", ""))
        review = reviewer(question, answer, trace)
    return {"question": question, "plan": plan, "trace": trace,
            "answer": answer, "review": review, "retried": retried}
