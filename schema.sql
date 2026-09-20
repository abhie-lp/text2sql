CREATE TABLE student(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(127),
  class VARCHAR(31), -- branch/department in uppercase: CSE, DS, ML, AI
  section VARCHAR(7), -- uppercase A, B, C, etc
  marks INT
)
