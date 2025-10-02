import sys
import json
import csv
import re
import os
import sqlite3
import shutil
from datetime import datetime


class Person:
    def __init__(self, name, age, _email):
        self.name = name
        self.age = age
        self._email = _email
    def introduce(self):
        print("My name is " + self.name + ". I am " + str(self.age) + " years old.")



class Student(Person):
    def __init__(self, name, age, _email, student_id):
        Person.__init__(self, name, age, _email)
        self.student_id = student_id
        self.registered_courses = []
    def register_course(self, course):
        self.registered_courses.append(course)

class Instructor(Person):
    def __init__(self, name, age, _email, instructor_id):
        Person.__init__(self, name, age, _email)
        self.instructor_id = instructor_id
        self.assigned_courses = []
    def assign_course(self, course):
        self.assigned_courses.append(course)

class Course:
    def __init__(self, course_id, course_name, instructor):
        self.course_id = course_id
        self.course_name = course_name
        self.instructor = instructor
        self.enrolled_students = []
    def add_student(self, student):
        self.enrolled_students.append(student)



def is_valid_email(x):
    p = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    m = re.match(p, x)
    if m:
        return True
    else:
        return False



def is_valid_age(x):
    try:
        v = int(x)
    except:
        return False
    if v >= 0:
        
        return True
    else:
        return False


students = []
instructors = []
courses = []

dbPath = "school.db"
conn = None

def init_db(path):
    global conn
    needCreate = not os.path.exists(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS students(
        student_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        _email TEXT
    )""")
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS instructors(
        instructor_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        _email TEXT
    )""")
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS courses(
        course_id TEXT PRIMARY KEY,
        course_name TEXT,
        instructor_id TEXT,
        FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id)
            ON UPDATE CASCADE ON DELETE SET NULL
    )""")
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS registrations(
        student_id TEXT,
        course_id TEXT,
        PRIMARY KEY(student_id, course_id),
        FOREIGN KEY(student_id) REFERENCES students(student_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
            ON UPDATE CASCADE ON DELETE CASCADE
    )""")
    
    conn.commit()

def reload_from_db():
    students[:] = []
    instructors[:] = []
    courses[:] = []
    insById = {}
    crsById = {}
    stuById = {}
    
    c1 = conn.execute("SELECT instructor_id, name, age, _email FROM instructors")
    for r in c1.fetchall():
        ins = Instructor(r["name"], r["age"], r["_email"], r["instructor_id"])
        instructors.append(ins)
        insById[ins.instructor_id] = ins
    c2 = conn.execute("SELECT course_id, course_name, instructor_id FROM courses")
    
    for r in c2.fetchall():
        insObj = None
        if r["instructor_id"] in insById:
            insObj = insById[r["instructor_id"]]
        c = Course(r["course_id"], r["course_name"], insObj)
        courses.append(c)
        crsById[c.course_id] = c
        if insObj:
            found = False
            for k in insObj.assigned_courses:
                if k.course_id == c.course_id:
                    found = True
            if not found:
                
                insObj.assign_course(c)
    c3 = conn.execute("SELECT student_id, name, age, _email FROM students")
    
    
    
    
    for r in c3.fetchall():
        s = Student(r["name"], r["age"], r["_email"], r["student_id"])
        students.append(s)
        stuById[s.student_id] = s
    c4 = conn.execute("SELECT student_id, course_id FROM registrations")
    
    
    
    
    
    
    
    for r in c4.fetchall():
        s = stuById.get(r["student_id"])
        c = crsById.get(r["course_id"])
        if s and c:
            foundA = False
            for k in s.registered_courses:
                if k.course_id == c.course_id:
                    foundA = True
            if not foundA:
                s.register_course(c)
            foundB = False
            for k in c.enrolled_students:
                if k.student_id == s.student_id:
                    foundB = True
            if not foundB:
                c.add_student(s)
                
def exists_student(sid):
    q = conn.execute("SELECT 1 FROM students WHERE student_id = ?", (sid,))
    r = q.fetchone()
    if r:
        return True
    else:
        return False

def exists_instructor(iid):
    q = conn.execute("SELECT 1 FROM instructors WHERE instructor_id = ?", (iid,))
    r = q.fetchone()
    if r:
        return True
    else:
        return False
    
def exists_course(cid):
    q = conn.execute("SELECT 1 FROM courses WHERE course_id = ?", (cid,))
    r = q.fetchone()
    if r:
        return True
    else:
        
        return False

def db_add_student(n, a, e, sid):
    if exists_student(sid):
        
        return False
    conn.execute("INSERT INTO students(student_id, name, age, _email) VALUES(?,?,?,?)", (sid, n, int(a), e))
    conn.commit()
    return True

def db_add_instructor(n, a, e, iid):
    if exists_instructor(iid):
        
        return False
    conn.execute("INSERT INTO instructors(instructor_id, name, age, _email) VALUES(?,?,?,?)", (iid, n, int(a), e))
    conn.commit()
    return True

def db_add_course(cid, cname, insId):
    if exists_course(cid):
        return False
    okIns = exists_instructor(insId)
    if not okIns:
        return False
    conn.execute("INSERT INTO courses(course_id, course_name, instructor_id) VALUES(?,?,?)", (cid, cname, insId))
    conn.commit()
    return True

def db_register(sid, cid):
    okS = exists_student(sid)
    
    if not okS:
        return False
    okC = exists_course(cid)
    if not okC:
        return False
    q = conn.execute("SELECT 1 FROM registrations WHERE student_id=? AND course_id=?", (sid, cid))
    r = q.fetchone()
    if r:
        return True
    conn.execute("INSERT INTO registrations(student_id, course_id) VALUES(?,?)", (sid, cid))
    conn.commit()
    return True

def db_assign_instructor(cid, iid):
    okC = exists_course(cid)
    if not okC:
        return False
    
    okI = exists_instructor(iid)
    if not okI:
        return False
    conn.execute("UPDATE courses SET instructor_id = ? WHERE course_id = ?", (iid, cid))
    conn.commit()
    return True

def db_update_student(oldId, newName, newAge, newEmail, newId):
    if newId != oldId:
        if exists_student(newId):
            return False
    conn.execute("UPDATE registrations SET student_id=? WHERE student_id=?", (newId, oldId))
    conn.execute("UPDATE students SET student_id=?, name=?, age=?, _email=? WHERE student_id=?", (newId, newName, int(newAge), newEmail, oldId))
    conn.commit()
    
    return True

def db_update_instructor(oldId, newName, newAge, newEmail, newId):
    if newId != oldId:
        if exists_instructor(newId):
            return False
    conn.execute("UPDATE instructors SET instructor_id=?, name=?, age=?, _email=? WHERE instructor_id=?", (newId, newName, int(newAge), newEmail, oldId))
    conn.commit()
    return True

def db_update_course(oldId, newId, newName, newInsId):
    if newId != oldId:
        if exists_course(newId):
            return False
        
    okI = exists_instructor(newInsId)
    if not okI:
        return False
    conn.execute("UPDATE registrations SET course_id=? WHERE course_id=?", (newId, oldId))
    conn.execute("UPDATE courses SET course_id=?, course_name=?, instructor_id=? WHERE course_id=?", (newId, newName, newInsId, oldId))
    conn.commit()
    
    return True

def db_delete_student(sid):
    conn.execute("DELETE FROM students WHERE student_id = ?", (sid,))
    conn.commit()
    
    return True

def db_delete_instructor(iid):
    conn.execute("UPDATE courses SET instructor_id = NULL WHERE instructor_id = ?", (iid,))
    conn.execute("DELETE FROM instructors WHERE instructor_id = ?", (iid,))
    conn.commit()
    
    return True


def db_delete_course(cid):
    conn.execute("DELETE FROM courses WHERE course_id = ?", (cid,))
    conn.commit()
    return True

def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outName = "backup_school_" + ts + ".db"
    shutil.copyfile(dbPath, outName)
    return outName
def export_csv():
    with open("students.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id","name","age","_email","courses"])
        for s in students:
            w.writerow([s.student_id, s.name, s.age, s._email,
                        ",".join(c.course_id for c in s.registered_courses)])
    with open("instructors.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instructor_id","name","age","_email","courses"])
        for ins in instructors:
            w.writerow([ins.instructor_id, ins.name, ins.age, ins._email,
                        ",".join(c.course_id for c in ins.assigned_courses)])
    with open("courses.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["course_id","course_name","instructor_id","enrolled_count"])
        for c in courses:
            iid = c.instructor.instructor_id if c.instructor else ""
            w.writerow([c.course_id, c.course_name, iid, len(c.enrolled_students)])
    return True
