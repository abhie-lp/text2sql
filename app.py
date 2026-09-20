import atexit

from dotenv import load_dotenv

load_dotenv()
import os
import sqlite3

import streamlit as st
from google.genai import Client, types

# Configure
MODEL = os.environ["GEMINI_MODEL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DB_URI = "file:student.db?mode=ro"
SCHEMA = ""
with open("./schema.sql") as f:
    SCHEMA = f.read()
PROMPT = f"""
You are a Text-to-SQL generator.
Your ONLY job:
Convert the input question into a valid SQLite SQL Query.
Database schema:
    {SCHEMA}

Rules:
- Only use tables and columns provided above.
- Generate SELECT queries only.
- Never INSERT, UPDATE, DELETE, DROP, ALTER or CREATE.
- Return ONLY the SQL query.
- Do not use markdown.
- Do not explain the query.

For example, the output of:
    - "How many entries of records are present?" is "SELECT COUNT(*) from student;"
    - "All the students studying in ds class?" is "SELECT * FROM student WHERE class='DS';"
    - "Names of students in section a" is "SELECT name FROM student WHERE section='A'"

"""
CONFIG = types.GenerateContentConfig(system_instruction=PROMPT)


SKIP = ("tts", "image", "transcribe", "computer-use", "robotics", "omni", "customtools", "pro")


@st.cache_data(ttl=3600)
def list_models() -> list[str]:
    names = (
        m.name.removeprefix("models/")
        for m in get_client().models.list()
        if m.name.startswith("gemini") or "generateContent" in (m.supported_actions or [])
    )
    return [n for n in names if not any(s in n for s in SKIP)]


@st.cache_resource
def get_client() -> Client:
    client = Client(api_key=GEMINI_API_KEY)
    atexit.register(client.close)
    return client


def get_gemini_response(question, model) -> str:
    # Provide SQL query as respone
    resp = get_client().models.generate_content(
        model=model,
        contents=question,
        config=CONFIG,
    )
    return resp.text


def read_sql_squery(sql):
    # Retrieve data from the db
    conn = sqlite3.connect(DB_URI, uri=True)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


st.set_page_config(page_title="Ask about the student data.")
st.header("App to retrieve the data of student")
question = st.text_input("Input: ", key="input", placeholder="Question about student.")
submit = st.button("Ask!")
models = list_models()
model = st.sidebar.selectbox("Model", models, index=models.index(MODEL) if MODEL in models else 0)

if question or submit:
    try:
        sql = get_gemini_response(question, model)
        st.code(sql, language="sql")
        st.subheader("The response is:")
        st.dataframe(read_sql_squery(sql))
    except Exception as e:
        st.error(f"Query failed: {e}")
