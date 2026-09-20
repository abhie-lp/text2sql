from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import os
import sqlite3

from google.genai import Client, types

# Configure
MODEL = "gemini-flash-latest"
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DB_URI = "file:student.db?mode=ro"


def get_gemini_response(question):
    # Provide SQL query as respone
    with Client(api_key=GEMINI_API_KEY) as client:
        resp = client.models.generate_content(
            model=MODEL,
            contents=question,
            config=types.GenerateContentConfig(system_instruction=PROMPT),
        )
        return resp.text


def read_sql_squery(sql):
    # Retrieve data from the db
    conn = sqlite3.connect(DB_URI, uri=True)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


PROMPT = """
You are an EXPERT in the only job of converting English questions to SQL query!
The SQL database as the name 'student' and has the following columns: [name, class, section, marks].
For example, the output of:
    - "How many entries of records are present?" is "SELECT COUNT(*) from student;"
    - "All the students studying in DS class?" is "SELECT * FROM student WHERE class='DS';"

The SQL output should be a valid SQL statement with no quotation marks of any kind enclosing the entire statement.
"""


st.set_page_config(page_title="I can retrieve any SQL query.")
st.header("Gemini App to retrieve the SQL data")
question = st.text_input("Input: ", key="input")
submit = st.button("Ask!")

if question or submit:
    sql = get_gemini_response(question)
    st.code(sql, language="sql")
    try:
        data = read_sql_squery(sql)
        st.subheader("The response is:")
        st.dataframe(data)
    except Exception as e:
        st.error(f"Query failed: {e}")
