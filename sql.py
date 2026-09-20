import sqlite3
from contextlib import closing

# Connect to sqlite and create the table
with closing(sqlite3.connect("./student.db")) as conn:
    cur = conn.cursor()
    with open("./schema.sql") as f:
        cur.executescript(f.read())
    conn.commit()
