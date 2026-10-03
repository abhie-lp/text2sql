import sqlglot
import atexit
import os
import re
import sqlite3
from textwrap import indent
from typing import TypedDict

import pandas as pd
import sqlglot
import streamlit as st
from dotenv import load_dotenv
from google.genai import Client, types
from sqlglot import exp

load_dotenv()

# Configure
MODEL = os.environ["GEMINI_MODEL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DB_URI = "file:student.db?mode=ro"
RE_PATTERN = r"""
^\s*PRAGMA\b.*?;\s* |
^\s*CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+ |
^\s*(?:UNIQUE|CHECK)\s*\([^;\n]*\),?\s*\n |
^\s*CREATE\s+INDEX\b.*?;\s*
"""
PROMPT = ""
with open("./prompt.txt") as fp, open("./schema.sql") as fs:
    PROMPT = fp.read().replace(
        "{SCHEMA}",
        indent(
            re.sub(
                RE_PATTERN,
                "",
                fs.read(),
                flags=re.IGNORECASE | re.MULTILINE | re.DOTALL | re.VERBOSE,
            ),
            "  ",
        ),
    )

SKIP = ("tts", "image", "transcribe", "computer-use", "robotics", "omni", "customtools", "pro")


@st.cache_data(ttl=3600)
def list_models() -> list[str]:
    names = (
        m.name.removeprefix("models/")
        for m in get_client().models.list()
        if "generateContent" in (m.supported_actions or [])
    )
    return [n for n in names if n.startswith("gemini") and not any(s in n for s in SKIP)]


@st.cache_resource
def get_client() -> Client:
    client = Client(api_key=GEMINI_API_KEY)
    atexit.register(client.close)
    return client


class QueryResult(TypedDict):
    question: str
    sql: str


class Queries(TypedDict):
    queries: list[QueryResult]


CONFIG = types.GenerateContentConfig(
    system_instruction=PROMPT,
    response_mime_type="application/json",
    response_schema=Queries,
)


def get_gemini_response(question, model) -> Queries:
    # Provide SQL query as respone
    resp = get_client().models.generate_content(
        model=model,
        contents=question,
        config=CONFIG,
    )
    return resp.parsed


def format_sql(sql: str) -> str:
    return sqlglot.transpile(sql, pretty=True, indent=2)[0]


def validate_sql(sql: str):
    # parse the sql as SQLite and raise ParseError on invalid syntax
    stmts = [s for s in sqlglot.parse(sql, read="sqlite") if s]
    if len(stmts) != 1:
        raise ValueError("Exactly one SQL statement is allowed.")

    if not isinstance(stmts[0], (exp.Select, exp.Union)):
        raise ValueError("Only SELECT queries are allowed.")
    return sql


def read_sql_query(sql: str) -> tuple[list[str], list]:
    # Retrieve data from the db
    validate_sql(sql)
    conn = sqlite3.connect(DB_URI, uri=True)
    try:
        cur = conn.execute(sql)
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        return columns, rows
    finally:
        conn.close()


models = list_models()
st.set_page_config(page_title="Ask about the student data.")
st.header("App to retrieve the data of student")
with st.form("query_form"):
    question = st.text_input(
        "What do you want to know?",
        placeholder="What do you want to know?",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("Ask!")

    with col2:
        model = st.selectbox(
            "Model",
            models,
            index=models.index(MODEL) if MODEL in models else 0,
            label_visibility="collapsed",
            width="stretch",
        )

if submit and question.strip():
    try:
        with st.spinner("Generating SQL..."):
            result: Queries = get_gemini_response(question, model)
    except Exception as e:
        st.error(f"Failed to generate query: {e}")
    else:
        for query in result["queries"]:
            st.markdown(f"#### {query['question']}")
            with st.expander("View SQL:"):
                st.code(format_sql(query["sql"]), language="sql")
            try:
                columns, rows = read_sql_query(query["sql"])
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df, column_order=columns, width="stretch", hide_index=True)
            except (sqlite3.Error, ValueError) as e:
                st.error(f"SQL failed: {e}")
