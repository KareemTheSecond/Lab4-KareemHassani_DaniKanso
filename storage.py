
"""Storage operations for the School Management System.

Provides JSON serialization, CSV export, and SQLite database persistence
for the School data model.
"""

import json, csv, shutil, time
from pathlib import Path
from typing import Tuple
from models import School
import sqlite3

DB_PATH = Path("school.db")

def save_json(school: School, path: str | Path):
    """Save school data to a JSON file.
    
    :param school: School object to serialize.
    :type school: School
    :param path: File path to write to.
    :type path: str | Path
    """
    path = Path(path)
    path.write_text(json.dumps(school.to_dict(), indent=2), encoding="utf-8")

def load_json(path: str | Path) -> School:
    """Load school data from a JSON file.
    
    :param path: File path to read from.
    :type path: str | Path
    :return: Reconstructed School object.
    :rtype: School
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return School.from_dict(data)

def export_csv(school: School, folder: str | Path):
    """Export school data to separate CSV files.
    
    Creates students.csv, instructors.csv, and courses.csv in the target folder.
    
    :param school: School object to export.
    :type school: School
    :param folder: Directory to write CSV files to.
    :type folder: str | Path
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    # Students
    with (folder / "students.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id","name","age","email","registered_courses"])
        for s in school.students.values():
            w.writerow([s.student_id,s.name,s.age,s._email,";".join(s.registered_courses)])
    # Instructors
    with (folder / "instructors.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instructor_id","name","age","email","assigned_courses"])
        for i in school.instructors.values():
            w.writerow([i.instructor_id,i.name,i.age,i._email,";".join(i.assigned_courses)])
    # Courses
    with (folder / "courses.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["course_id","course_name","instructor_id","enrolled_students"])
        for c in school.courses.values():
            w.writerow([c.course_id,c.course_name,c.instructor_id or "", ";".join(c.enrolled_students)])

# ---------------------- SQLite ----------------------
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the SQLite database with required tables.
    
    Creates students, instructors, courses, and registrations tables
    with appropriate foreign key constraints.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age >= 0),
            email TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS instructors (
            instructor_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age >= 0),
            email TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS courses (
            course_id TEXT PRIMARY KEY,
            course_name TEXT NOT NULL,
            instructor_id TEXT,
            FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS registrations (
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            PRIMARY KEY (student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()

def school_to_db(school: School):
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    # Upsert instructors
    for i in school.instructors.values():
        cur.execute("""INSERT INTO instructors(instructor_id,name,age,email)
                       VALUES(?,?,?,?)
                       ON CONFLICT(instructor_id) DO UPDATE SET name=excluded.name, age=excluded.age, email=excluded.email""",
                    (i.instructor_id, i.name, i.age, i._email))
    # Upsert students
    for s in school.students.values():
        cur.execute("""INSERT INTO students(student_id,name,age,email)
                       VALUES(?,?,?,?)
                       ON CONFLICT(student_id) DO UPDATE SET name=excluded.name, age=excluded.age, email=excluded.email""",
                    (s.student_id, s.name, s.age, s._email))
    # Upsert courses
    for c in school.courses.values():
        cur.execute("""INSERT INTO courses(course_id,course_name,instructor_id)
                       VALUES(?,?,?)
                       ON CONFLICT(course_id) DO UPDATE SET course_name=excluded.course_name, instructor_id=excluded.instructor_id""",
                    (c.course_id, c.course_name, c.instructor_id))
        # registrations
        cur.execute("DELETE FROM registrations WHERE course_id=?", (c.course_id,))
        for sid in c.enrolled_students:
            cur.execute("INSERT OR IGNORE INTO registrations(student_id,course_id) VALUES(?,?)", (sid, c.course_id))
    conn.commit()
    conn.close()

def db_to_school() -> School:
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    sc = School()
    # Instructors
    for row in cur.execute("SELECT instructor_id,name,age,email FROM instructors"):
        from models import Instructor
        ins = Instructor(name=row[1], age=row[2], _email=row[3], instructor_id=row[0])
        sc.add_instructor(ins)
    # Students
    for row in cur.execute("SELECT student_id,name,age,email FROM students"):
        from models import Student
        st = Student(name=row[1], age=row[2], _email=row[3], student_id=row[0])
        sc.add_student(st)
    # Courses
    from models import Course
    for row in cur.execute("SELECT course_id,course_name,instructor_id FROM courses"):
        c = Course(course_id=row[0], course_name=row[1], instructor_id=row[2] or None)
        sc.add_course(c)
    # Registrations
    for row in cur.execute("SELECT student_id, course_id FROM registrations"):
        sc.register_student_in_course(row[0], row[1])
    conn.close()
    return sc

def backup_db(dest_folder: str | Path) -> Path:
    init_db()
    dest_folder = Path(dest_folder)
    dest_folder.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup_path = dest_folder / f"school-backup-{ts}.db"
    shutil.copyfile(DB_PATH, backup_path)
    return backup_path
