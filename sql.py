import sqlite3

# Connect to sqlite
conn = sqlite3.connect("student.db")

# Create a cursor object
cur = conn.cursor()

# Create a table
table_info = """
CREATE TABLE IF NOT EXISTS student(
    name VARCHAR(127),
    class VARCHAR(31),
    section VARCHAR(31),
    marks INT
);
"""

cur.execute(table_info)

# Insert some records
cur.execute("INSERT INTO student VALUES('Abhishek', 'CSE', 'A', 80)")
cur.execute("INSERT INTO student VALUES('Moolchand', 'CSE', 'B', 60)")
cur.execute("INSERT INTO student VALUES('Laajo', 'DS', 'A', 99)")
cur.execute("INSERT INTO student VALUES('Samosa', 'DS', 'B', 85)")
cur.execute("INSERT INTO student VALUES('Bilawal', 'ML', 'A', 90)")
cur.execute("INSERT INTO student VALUES('Mariyam', 'ML', 'B', 50)")

# Display the records
print("Inserted records are")
data = cur.execute("SELECT * FROM student")

for i, row in enumerate(data, 1):
    print(i, "=>", *row, sep=", ")

# Close the connection
conn.commit()
conn.close()
