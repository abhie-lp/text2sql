import atexit

import sqlglot
from dotenv import load_dotenv

load_dotenv()
import os
import sqlite3
from typing import TypedDict

import pandas as pd
import streamlit as st
from google.genai import Client, types
from sqlglot import exp

# Configure
MODEL = os.environ["GEMINI_MODEL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DB_URI = "file:student.db?mode=ro"
PROMPT = ""
with open("./prompt.txt") as fp, open("./schema.sql") as fs:
    PROMPT = fp.read().replace("{SCHEMA}", fs.read())

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


def validate_sql(sql: str):
    # parse the sql as SQLite and raise ParseError on invalid syntax
    stmts = [s for s in sqlglot.parse(sql, read="sqlite") if s]
    if len(stmts) != 1:
        raise ValueError("Exactly one SQL statement is allowed.")

    if not isinstance(stmts[0], (exp.Select, exp.Union)):
        raise ValueError("Only SELECt queries are allowed.")
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


st.set_page_config(page_title="Ask about the student data.")
st.header("App to retrieve the data of student")
with st.form("query_form"):
    question = st.text_input("Input: ", placeholder="Question about student.")
    submit = st.form_submit_button("Ask!")
models = list_models()
model = st.sidebar.selectbox("Model", models, index=models.index(MODEL) if MODEL in models else 0)

if submit and question.strip():
    try:
        result: Queries = get_gemini_response(question, model)
    except Exception as e:
        st.error(f"Failed to generate query: {e}")
    else:
        for query in result["queries"]:
            st.markdown(f"#### {query['question'].capitalize()}")
            st.code(query["sql"], language="sql")
            try:
                columns, rows = read_sql_query(query["sql"])
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df, column_order=columns, width="stretch", hide_index=True)
            except (sqlite3.Error, ValueError) as e:
                st.error(f"SQL failed: {e}")
