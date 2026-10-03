PRAGMA foreign_keys = ON;

-- Academic departments/branches: CSE, AI, DS, AIML, etc
CREATE TABLE IF NOT EXISTS department(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code VARCHAR(15) UNIQUE NOT NULL,
  name VARCHAR(127) NOT NULL
);

-- Academic years/sessions: 2025-26, 2026-27, etc
CREATE TABLE IF NOT EXISTS academic_session(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(31) NOT NULL UNIQUE,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  CHECK (start_date <  end_date)
);

-- The section assigned to student: A, B, C, D, etc
CREATE TABLE IF NOT EXISTS section(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(15) NOT NULL UNIQUE
);

-- Represents a section withing a specific academic session, department and semester
-- e.g: CSE / Semester 5 / A / 2026-27
CREATE TABLE IF NOT EXISTS academic_section(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  academic_session_id INTEGER NOT NULL,
  department_id INTEGER NOT NULL,
  semester INTEGER NOT NULL,
  section_id INTEGER NOT NULL,

  FOREIGN KEY (academic_session_id) REFERENCES academic_session(id) ON DELETE RESTRICT,
  FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE RESTRICT,
  FOREIGN KEY (section_id) REFERENCES section(id) ON DELETE RESTRICT,

  UNIQUE(academic_session_id, department_id, semester, section_id),
  CHECK (semester BETWEEN 1 AND 8)
);

-- Basic details of the student after joining
CREATE TABLE IF NOT EXISTS student(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  enrollment_number VARCHAR(31) NOT NULL UNIQUE,
  
  first_name VARCHAR(63) NOT NULL,
  last_name VARCHAR(63),

  dob DATE,
  gender VARCHAR(1), -- M: Male or F: Female
  
  email VARCHAR(127) UNIQUE,
  phone VARCHAR(20),

  admission_date DATE,

  CHECK (gender IN ('M', 'F'))
);

-- Students academic status for an academic session
CREATE TABLE IF NOT EXISTS student_academic(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  academic_section_id INTEGER NOT NULL,

  FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
  FOREIGN KEY (academic_section_id) REFERENCES academic_section(id) ON DELETE RESTRICT,
  UNIQUE (student_id, academic_section_id)
);

-- Courses/Subjects offered by academic departments, such as DAA, DBMS, Operating Systems, etc
CREATE TABLE IF NOT EXISTS course (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code VARCHAR(15) NOT NULL UNIQUE,
  name VARCHAR(127) NOT NULL,
  credits INT NOT NULL,
  department_id INTEGER NOT NULL,

  FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE RESTRICT,
  CHECK (credits > 0)
);

-- The courses a student is enrolled in for their academic session and semester
CREATE TABLE IF NOT EXISTS enrollment(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_academic_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,

  FOREIGN KEY (student_academic_id) REFERENCES student_academic(id) ON DELETE CASCADE,
  FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE RESTRICT,
  UNIQUE (student_academic_id, course_id)
);

-- Defines reusable assessment types such as CT-1, ASG-1, Mid-Term, etc.
-- An assessment type defines what kind of assessment is being conducted.
CREATE TABLE IF NOT EXISTS assessment_type(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code VARCHAR(15) NOT NULL UNIQUE,
  name VARCHAR(31) NOT NULL UNIQUE
);

-- Defines the fixed question pattern for an assessment type.
-- Linked to assessment_type: example, CT-1 can define 1-a, 1-b, ... 2-a, 2-b, 3
-- along with the maximum marks for each question.
CREATE TABLE IF NOT EXISTS assessment_type_question(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  assessment_type_id INTEGER NOT NULL,
  question_number VARCHAR(7) NOT NULL,
  max_marks NUMERIC NOT NULL,

  FOREIGN KEY (assessment_type_id) REFERENCES assessment_type(id) ON DELETE CASCADE,
  UNIQUE (assessment_type_id, question_number),
  UNIQUE (id, assessment_type_id),
  CHECK (length(trim(question_number)) > 0),
  CHECK (max_marks > 0)
);

-- Represents the actual occurrence of an assessment for a specific course, academic session and semester.
-- Linked to assessment_type to determine the assessment pattern/questions.
-- Example: CT-1 for DAA in semester 3 during the 2026-27 academic session.
CREATE TABLE IF NOT EXISTS assessment(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  assessment_type_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  academic_session_id INTEGER NOT NULL,
  semester INTEGER NOT NULL,
  assessment_date DATE NOT NULL,

  FOREIGN KEY (assessment_type_id) REFERENCES assessment_type(id) ON DELETE RESTRICT,
  FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE RESTRICT,
  FOREIGN KEY (academic_session_id) REFERENCES academic_session(id) ON DELETE RESTRICT,

  CHECK (semester BETWEEN 1 AND 8),
  UNIQUE (assessment_type_id, course_id, academic_session_id, semester),
  UNIQUE (id, assessment_type_id)
);

-- Links an actual assessment to the sections that are taking it.
-- One assessment can be conducted for multiple sections.
-- Example: the same CT-1 for DAA can be taken by sections A, B, C.
CREATE TABLE IF NOT EXISTS assessment_section(
  assessment_id INTEGER NOT NULL,
  academic_section_id INTEGER NOT NULL,

  PRIMARY KEY (assessment_id, academic_section_id),
  FOREIGN KEY (assessment_id) REFERENCES assessment(id) ON DELETE CASCADE,
  FOREIGN KEY (academic_section_id) REFERENCES academic_section(id) ON DELETE RESTRICT
);


-- Stores the result of one enrolled student for one actual assessment.
-- Linked to the assessment to identify the assessment and to enrollment to identify the student/course.
-- Also records whether the student was absent.
CREATE TABLE IF NOT EXISTS assessment_result (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  assessment_id INTEGER NOT NULL,
  enrollment_id INTEGER NOT NULL,
  assessment_type_id INTEGER NOT NULL,
  is_absent BOOLEAN NOT NULL DEFAULT FALSE,

  FOREIGN KEY (assessment_id) REFERENCES assessment(id) ON DELETE CASCADE,
  FOREIGN KEY (enrollment_id) REFERENCES enrollment(id) ON DELETE CASCADE,
  FOREIGN KEY (assessment_id, assessment_type_id) REFERENCES assessment(id, assessment_type_id) ON DELETE CASCADE,
  UNIQUE (id, assessment_type_id),
  UNIQUE (assessment_id, enrollment_id),
  CHECK (is_absent IN (0, 1))
);

-- Stores the marks obtained by a student for individual questions.
-- Linked to assessment_result to identify the student's result and to assessment_type_question to identify the question and its maximum marks.
-- Example: Student X scored 2 out 2.6 marks in question 2-a.
CREATE TABLE IF NOT EXISTS assessment_question_mark (
  assessment_result_id INTEGER NOT NULL,
  assessment_type_question_id INTEGER NOT NULL,
  assessment_type_id INTEGER NOT NULL,
  marks_obtained NUMERIC NOT NULL,

  PRIMARY KEY (assessment_result_id, assessment_type_question_id),
  FOREIGN KEY (assessment_result_id, assessment_type_id) REFERENCES assessment_result(id, assessment_type_id) ON DELETE CASCADE,
  FOREIGN KEY (assessment_type_question_id, assessment_type_id) REFERENCES assessment_type_question(id, assessment_type_id) ON DELETE RESTRICT,
  CHECK (marks_obtained >= 0)
);

-- Individual class/lecture sessions conducted for a course and section.
CREATE TABLE IF NOT EXISTS class_session (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL,
  academic_section_id INTEGER NOT NULL,
  session_date DATE NOT NULL,
  start_time TIME,
  end_time TIME,

  FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE RESTRICT,
  FOREIGN KEY (academic_section_id) REFERENCES academic_section(id) ON DELETE RESTRICT,
  UNIQUE (course_id, academic_section_id, session_date, start_time),
  CHECK (end_time IS NULL OR start_time IS NULL OR start_time < end_time)
);

-- The attendance status of each student for a particular class session.
CREATE TABLE IF NOT EXISTS attendance (
  class_session_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  status VARCHAR(15) NOT NULL,

  PRIMARY KEY (class_session_id, student_id),
  FOREIGN KEY (class_session_id) REFERENCES class_session(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
  CHECK (status IN ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED'))
);

CREATE INDEX IF NOT EXISTS idx_academic_section_session ON academic_section(academic_session_id);
CREATE INDEX IF NOT EXISTS idx_academic_section_department ON academic_section(department_id);
CREATE INDEX IF NOT EXISTS idx_academic_section_section ON academic_section(section_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_course ON enrollment(course_id);
CREATE INDEX IF NOT EXISTS idx_assessment_type_question_type ON assessment_type_question(assessment_type_id);
CREATE INDEX IF NOT EXISTS idx_assessment_course ON assessment(course_id);
CREATE INDEX IF NOT EXISTS idx_assessment_session ON assessment(academic_session_id);
CREATE INDEX IF NOT EXISTS idx_assessment_section_academic_section ON assessment_section(academic_section_id);
CREATE INDEX IF NOT EXISTS idx_assessment_result_enrollment ON assessment_result(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_question_mark_question ON assessment_question_mark(assessment_type_question_id);
CREATE INDEX IF NOT EXISTS idx_class_session_course_academic_section ON class_session(course_id, academic_section_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
