import sys
import json
import csv
import re
import os
import sqlite3
import shutil
from datetime import datetime
from PyQt5 import QtWidgets, QtCore

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
        email TEXT
    )""")
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS instructors(
        instructor_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        email TEXT
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
    
    c1 = conn.execute("SELECT instructor_id, name, age, email FROM instructors")
    for r in c1.fetchall():
        ins = Instructor(r["name"], r["age"], r["email"], r["instructor_id"])
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
    c3 = conn.execute("SELECT student_id, name, age, email FROM students")
    
    
    
    
    for r in c3.fetchall():
        s = Student(r["name"], r["age"], r["email"], r["student_id"])
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
    conn.execute("INSERT INTO students(student_id, name, age, email) VALUES(?,?,?,?)", (sid, n, int(a), e))
    conn.commit()
    return True

def db_add_instructor(n, a, e, iid):
    if exists_instructor(iid):
        
        return False
    conn.execute("INSERT INTO instructors(instructor_id, name, age, email) VALUES(?,?,?,?)", (iid, n, int(a), e))
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
    conn.execute("UPDATE students SET student_id=?, name=?, age=?, email=? WHERE student_id=?", (newId, newName, int(newAge), newEmail, oldId))
    conn.commit()
    
    return True

def db_update_instructor(oldId, newName, newAge, newEmail, newId):
    if newId != oldId:
        if exists_instructor(newId):
            return False
    conn.execute("UPDATE instructors SET instructor_id=?, name=?, age=?, email=? WHERE instructor_id=?", (newId, newName, int(newAge), newEmail, oldId))
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

def export_csv_qt():
    try:
        with open("students.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["student_id","name","age","email","courses"])
            for s in students:
                cids = []
                for c in s.registered_courses:
                    cids.append(c.course_id)
                    
                    
                    
                    
                    
                    
                    
                w.writerow([s.student_id, s.name, s.age, s._email, ",".join(cids)])
        with open("instructors.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["instructor_id","name","age","email","courses"])
            
            
            for ins in instructors:
                
                
                
                
                
                cids = []
                for c in ins.assigned_courses:
                    cids.append(c.course_id)
                w.writerow([ins.instructor_id, ins.name, ins.age, ins._email, ",".join(cids)])
        with open("courses.csv", "w", newline="", encoding="utf-8") as f:
            
            w = csv.writer(f)
            
            
            w.writerow(["course_id","course_name","instructor_id","enrolled_count"])
            for c in courses:
                iid = ""
                if c.instructor:
                    iid = c.instructor.instructor_id
                w.writerow([c.course_id, c.course_name, iid, len(c.enrolled_students)])
        QtWidgets.QMessageBox.information(None, "Export", "CSV files written")
    except:
        QtWidgets.QMessageBox.critical(None, "Error", "Export failed")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        
        
        
        
        self.setWindowTitle("School Management System")
        
        
        
        
        w = QtWidgets.QWidget()
        self.setCentralWidget(w)
        lay = QtWidgets.QVBoxLayout(w)

        addBox = QtWidgets.QGroupBox("Add Records")
        lay.addWidget(addBox)
        
        addLay = QtWidgets.QVBoxLayout(addBox)

        sRow = QtWidgets.QHBoxLayout()
        addLay.addLayout(sRow)
        self.studentNameEdit = QtWidgets.QLineEdit()
        self.studentAgeEdit = QtWidgets.QLineEdit()
        
        self.studentEmailEdit = QtWidgets.QLineEdit()
        self.studentIdEdit = QtWidgets.QLineEdit()
        sRow.addWidget(QtWidgets.QLabel("Student Name"))
        
        sRow.addWidget(self.studentNameEdit)
        sRow.addWidget(QtWidgets.QLabel("Age"))
        sRow.addWidget(self.studentAgeEdit)
        sRow.addWidget(QtWidgets.QLabel("Email"))
        sRow.addWidget(self.studentEmailEdit)
        
        sRow.addWidget(QtWidgets.QLabel("Student ID"))
        sRow.addWidget(self.studentIdEdit)
        
        self.addStudentBtn = QtWidgets.QPushButton("Add Student")
        sRow.addWidget(self.addStudentBtn)
        
        self.addStudentBtn.clicked.connect(self.add_student_qt)


        iRow = QtWidgets.QHBoxLayout()
        addLay.addLayout(iRow)
        
        self.instructorNameEdit = QtWidgets.QLineEdit()
        self.instructorAgeEdit = QtWidgets.QLineEdit()
        self.instructorEmailEdit = QtWidgets.QLineEdit()
        
        self.instructorIdEdit = QtWidgets.QLineEdit()
        iRow.addWidget(QtWidgets.QLabel("Instructor Name"))
        iRow.addWidget(self.instructorNameEdit)
        iRow.addWidget(QtWidgets.QLabel("Age"))
        iRow.addWidget(self.instructorAgeEdit)
        iRow.addWidget(QtWidgets.QLabel("Email"))
        
        iRow.addWidget(self.instructorEmailEdit)
        iRow.addWidget(QtWidgets.QLabel("Instructor ID"))
        iRow.addWidget(self.instructorIdEdit)
        self.addInstructorBtn = QtWidgets.QPushButton("Add Instructor")
        iRow.addWidget(self.addInstructorBtn)
        self.addInstructorBtn.clicked.connect(self.add_instructor_qt)
        

        cRow = QtWidgets.QHBoxLayout()
        addLay.addLayout(cRow)
        self.courseIdEdit = QtWidgets.QLineEdit()
        self.courseNameEdit = QtWidgets.QLineEdit()
        self.courseInstructorCombo = QtWidgets.QComboBox()
        cRow.addWidget(QtWidgets.QLabel("Course ID"))
        cRow.addWidget(self.courseIdEdit)
        
        cRow.addWidget(QtWidgets.QLabel("Course Name"))
        cRow.addWidget(self.courseNameEdit)
        cRow.addWidget(QtWidgets.QLabel("Instructor"))
        cRow.addWidget(self.courseInstructorCombo)
        
        self.addCourseBtn = QtWidgets.QPushButton("Add Course")
        cRow.addWidget(self.addCourseBtn)
        self.addCourseBtn.clicked.connect(self.add_course_qt)

        opsBox = QtWidgets.QGroupBox("Operations")
        
        lay.addWidget(opsBox)
        opsLay = QtWidgets.QHBoxLayout(opsBox)
        self.studentSelectCombo = QtWidgets.QComboBox()
        self.courseSelectCombo = QtWidgets.QComboBox()
        self.registerBtn = QtWidgets.QPushButton("Register Student")
        opsLay.addWidget(QtWidgets.QLabel("Student"))
        opsLay.addWidget(self.studentSelectCombo)
        opsLay.addWidget(QtWidgets.QLabel("Course"))
        opsLay.addWidget(self.courseSelectCombo)
        opsLay.addWidget(self.registerBtn)
        self.registerBtn.clicked.connect(self.register_student_qt)

        self.instructorSelectCombo = QtWidgets.QComboBox()
        self.courseAssignCombo = QtWidgets.QComboBox()
        
        self.assignBtn = QtWidgets.QPushButton("Assign Instructor")
        opsLay.addWidget(QtWidgets.QLabel("Instructor"))
        opsLay.addWidget(self.instructorSelectCombo)
        opsLay.addWidget(QtWidgets.QLabel("Course"))
        
        opsLay.addWidget(self.courseAssignCombo)
        opsLay.addWidget(self.assignBtn)
        self.assignBtn.clicked.connect(self.assign_instructor_qt)
        

        recBox = QtWidgets.QGroupBox("Records")
        lay.addWidget(recBox)
        recLay = QtWidgets.QVBoxLayout(recBox)
        self.studentTable = QtWidgets.QTableWidget(0, 5)
        self.studentTable.setHorizontalHeaderLabels(["student_id","name","age","email","courses"])
        
        recLay.addWidget(self.studentTable)
        self.instructorTable = QtWidgets.QTableWidget(0, 5)
        self.instructorTable.setHorizontalHeaderLabels(["instructor_id","name","age","email","courses"])
        
        recLay.addWidget(self.instructorTable)
        self.courseTable = QtWidgets.QTableWidget(0, 4)
        
        self.courseTable.setHorizontalHeaderLabels(["course_id","course_name","instructor_id","enrolled_count"])
        recLay.addWidget(self.courseTable)

        actRow = QtWidgets.QHBoxLayout()
        recLay.addLayout(actRow)
        self.editBtn = QtWidgets.QPushButton("Edit Selected")
        self.deleteBtn = QtWidgets.QPushButton("Delete Selected")
        actRow.addWidget(self.editBtn)
        
        actRow.addWidget(self.deleteBtn)
        self.editBtn.clicked.connect(self.edit_selected_qt)
        self.deleteBtn.clicked.connect(self.delete_selected_qt)


        searchBox = QtWidgets.QGroupBox("Search")
        lay.addWidget(searchBox)
        sLay = QtWidgets.QHBoxLayout(searchBox)
        self.searchEdit = QtWidgets.QLineEdit()
        self.searchTypeCombo = QtWidgets.QComboBox()
        self.searchTypeCombo.addItems(["Student","Instructor","Course"])
        self.searchBtn = QtWidgets.QPushButton("Search")
        self.resetBtn = QtWidgets.QPushButton("Reset")
        sLay.addWidget(QtWidgets.QLabel("Term"))
        
        sLay.addWidget(self.searchEdit)
        sLay.addWidget(self.searchTypeCombo)
        sLay.addWidget(self.searchBtn)
        sLay.addWidget(self.resetBtn)
        
        self.searchBtn.clicked.connect(self.do_search_qt)
        self.resetBtn.clicked.connect(self.reset_search_qt)

        ioRow = QtWidgets.QHBoxLayout()
        lay.addLayout(ioRow)
        
        self.saveBtn = QtWidgets.QPushButton("Save")
        
        self.loadBtn = QtWidgets.QPushButton("Load")
        self.exportBtn = QtWidgets.QPushButton("Export CSV")
        self.backupBtn = QtWidgets.QPushButton("Backup DB")
        ioRow.addWidget(self.saveBtn)
        ioRow.addWidget(self.loadBtn)
        ioRow.addWidget(self.exportBtn)
        ioRow.addWidget(self.backupBtn)
        self.saveBtn.clicked.connect(self.save_now)
        self.loadBtn.clicked.connect(self.load_now)
        self.exportBtn.clicked.connect(export_csv_qt)
        self.backupBtn.clicked.connect(self.backup_now)

        init_db(dbPath)
        reload_from_db()
        self.refresh_views()

    def refresh_views(self, fs=None, fi=None, fc=None):
        self.courseInstructorCombo.clear()
        for ins in instructors:
            self.courseInstructorCombo.addItem(ins.instructor_id)
        self.studentSelectCombo.clear()
        for s in students:
            
            self.studentSelectCombo.addItem(s.student_id)
        self.courseSelectCombo.clear()
        for c in courses:
            self.courseSelectCombo.addItem(c.course_id)
        self.instructorSelectCombo.clear()
        for ins in instructors:
            self.instructorSelectCombo.addItem(ins.instructor_id)
            
        self.courseAssignCombo.clear()
        for c in courses:
            self.courseAssignCombo.addItem(c.course_id)
        self.studentTable.setRowCount(0)
        useS = students
        if fs is not None:
            useS = fs
        for s in useS:
            cids = []
            for c in s.registered_courses:
                cids.append(c.course_id)
            r = self.studentTable.rowCount()
            self.studentTable.insertRow(r)
            self.studentTable.setItem(r, 0, QtWidgets.QTableWidgetItem(s.student_id))
            self.studentTable.setItem(r, 1, QtWidgets.QTableWidgetItem(s.name))
            
            self.studentTable.setItem(r, 2, QtWidgets.QTableWidgetItem(str(s.age)))
            self.studentTable.setItem(r, 3, QtWidgets.QTableWidgetItem(s._email))
            self.studentTable.setItem(r, 4, QtWidgets.QTableWidgetItem(",".join(cids)))
            
        self.instructorTable.setRowCount(0)
        useI = instructors
        if fi is not None:
            useI = fi
        for ins in useI:
            cids = []
            for c in ins.assigned_courses:
                cids.append(c.course_id)
            r = self.instructorTable.rowCount()
            self.instructorTable.insertRow(r)
            self.instructorTable.setItem(r, 0, QtWidgets.QTableWidgetItem(ins.instructor_id))
            self.instructorTable.setItem(r, 1, QtWidgets.QTableWidgetItem(ins.name))
            self.instructorTable.setItem(r, 2, QtWidgets.QTableWidgetItem(str(ins.age)))
            self.instructorTable.setItem(r, 3, QtWidgets.QTableWidgetItem(ins._email))
            
            self.instructorTable.setItem(r, 4, QtWidgets.QTableWidgetItem(",".join(cids)))
        self.courseTable.setRowCount(0)
        useC = courses
        if fc is not None:
            useC = fc
        for c in useC:
            iid = ""
            if c.instructor:
                iid = c.instructor.instructor_id
            r = self.courseTable.rowCount()
            self.courseTable.insertRow(r)
            self.courseTable.setItem(r, 0, QtWidgets.QTableWidgetItem(c.course_id))
            self.courseTable.setItem(r, 1, QtWidgets.QTableWidgetItem(c.course_name))
            self.courseTable.setItem(r, 2, QtWidgets.QTableWidgetItem(iid))
            self.courseTable.setItem(r, 3, QtWidgets.QTableWidgetItem(str(len(c.enrolled_students))))

    def add_student_qt(self):
        n = self.studentNameEdit.text().strip()
        a = self.studentAgeEdit.text().strip()
        e = self.studentEmailEdit.text().strip()
        i = self.studentIdEdit.text().strip()
        if n == "" or a == "" or e == "" or i == "":
            QtWidgets.QMessageBox.critical(self, "Error", "All fields required")
            return
        if not is_valid_age(a):
            QtWidgets.QMessageBox.critical(self, "Error", "Age must be non-negative integer")
            return
        if not is_valid_email(e):
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid email")
            return
        ok = db_add_student(n, a, e, i)
        
        if not ok:
            QtWidgets.QMessageBox.critical(self, "Error", "Student ID exists")
            
            return
        self.studentNameEdit.clear()
        self.studentAgeEdit.clear()
        self.studentEmailEdit.clear()
        self.studentIdEdit.clear()
        reload_from_db()
        self.refresh_views()

    def add_instructor_qt(self):
        n = self.instructorNameEdit.text().strip()
        a = self.instructorAgeEdit.text().strip()
        e = self.instructorEmailEdit.text().strip()
        i = self.instructorIdEdit.text().strip()
        if n == "" or a == "" or e == "" or i == "":
            QtWidgets.QMessageBox.critical(self, "Error", "All fields required")
            return
        if not is_valid_age(a):
            QtWidgets.QMessageBox.critical(self, "Error", "Age must be non-negative integer")
            return
        if not is_valid_email(e):
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid email")
            return
        ok = db_add_instructor(n, a, e, i)
        
        if not ok:
            QtWidgets.QMessageBox.critical(self, "Error", "Instructor ID exists")
            return
        self.instructorNameEdit.clear()
        self.instructorAgeEdit.clear()
        self.instructorEmailEdit.clear()
        self.instructorIdEdit.clear()
        reload_from_db()
        self.refresh_views()

    def add_course_qt(self):
        cid = self.courseIdEdit.text().strip()
        cname = self.courseNameEdit.text().strip()
        insId = self.courseInstructorCombo.currentText().strip()
        if cid == "" or cname == "" or insId == "":
            QtWidgets.QMessageBox.critical(self, "Error", "All fields required")
            return
        
        ok = db_add_course(cid, cname, insId)
        
        if not ok:
            QtWidgets.QMessageBox.critical(self, "Error", "Check Course ID and Instructor")
            
            return
        self.courseIdEdit.clear()
        self.courseNameEdit.clear()
        reload_from_db()
        self.refresh_views()

    def register_student_qt(self):
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        sid = self.studentSelectCombo.currentText().strip()
        cid = self.courseSelectCombo.currentText().strip()
        if sid == "" or cid == "":
            QtWidgets.QMessageBox.critical(self, "Error", "Select student and course")
            return
        ok = db_register(sid, cid)
        if not ok:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid selection")
            return
        reload_from_db()
        self.refresh_views()
        QtWidgets.QMessageBox.information(self, "OK", "Student registered")

    def assign_instructor_qt(self):
        
        iid = self.instructorSelectCombo.currentText().strip()
        cid = self.courseAssignCombo.currentText().strip()
        if iid == "" or cid == "":
            QtWidgets.QMessageBox.critical(self, "Error", "Select instructor and course")
            return
        ok = db_assign_instructor(cid, iid)
        if not ok:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid selection")
            return
        reload_from_db()
        self.refresh_views()
        QtWidgets.QMessageBox.information(self, "OK", "Instructor assigned")
        
        
        

    def do_search_qt(self):
        t = self.searchEdit.text().strip().lower()
        
        k = self.searchTypeCombo.currentText().strip()
        if t == "" or k == "":
            QtWidgets.QMessageBox.critical(self, "Error", "Enter term and type")
            return
        if k == "Student":
            lst = []
            for s in students:
                hit = False
                if t in s.name.lower() or t in s.student_id.lower() or t in s._email.lower():
                    hit = True
                if not hit:
                    for c in s.registered_courses:
                        if t in c.course_id.lower() or t in c.course_name.lower():
                            hit = True
                if hit:
                    lst.append(s)
            self.refresh_views(fs=lst, fi=None, fc=None)
            return
        if k == "Instructor":
            lst = []
            for ins in instructors:
                hit = False
                if t in ins.name.lower() or t in ins.instructor_id.lower() or t in ins._email.lower():
                    hit = True
                if not hit:
                    for c in ins.assigned_courses:
                        if t in c.course_id.lower() or t in c.course_name.lower():
                            hit = True
                if hit:
                    lst.append(ins)
            self.refresh_views(fs=None, fi=lst, fc=None)
            return
        lst = []
        for c in courses:
            hit = False
            if t in c.course_id.lower() or t in c.course_name.lower():
                hit = True
            if not hit and c.instructor:
                if t in c.instructor.instructor_id.lower() or t in c.instructor.name.lower():
                    hit = True
            if hit:
                lst.append(c)
        self.refresh_views(fs=None, fi=None, fc=lst)

    def reset_search_qt(self):
        self.searchEdit.clear()
        
        
        
        
        
        
        
        self.searchTypeCombo.setCurrentIndex(0)
        self.refresh_views()
        

    def edit_selected_qt(self):
        if self.studentTable.hasFocus():
            r = self.studentTable.currentRow()
            if r < 0:
                return
            sid = self.studentTable.item(r, 0).text()
            target = None
            for s in students:
                if s.student_id == sid:
                    target = s
            if target is None:
                return
            d = QtWidgets.QDialog(self)
            d.setWindowTitle("Edit Student")
            fl = QtWidgets.QFormLayout(d)
            nEdit = QtWidgets.QLineEdit(target.name)
            aEdit = QtWidgets.QLineEdit(str(target.age))
            eEdit = QtWidgets.QLineEdit(target._email)
            
            iEdit = QtWidgets.QLineEdit(target.student_id)
            fl.addRow("Name", nEdit)
            fl.addRow("Age", aEdit)
            fl.addRow("Email", eEdit)
            fl.addRow("Student ID", iEdit)
            bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
            fl.addRow(bb)
            def do_save():
                newName = nEdit.text().strip()
                newAge = aEdit.text().strip()
                newEmail = eEdit.text().strip()
                newId = iEdit.text().strip()
                if newName == "" or newAge == "" or newEmail == "" or newId == "":
                    return
                if not is_valid_age(newAge):
                    return
                if not is_valid_email(newEmail):
                    return
                ok = db_update_student(target.student_id, newName, newAge, newEmail, newId)
                if not ok:
                    return
                
                
                
                
                
                reload_from_db()
                self.refresh_views()
                d.accept()
            bb.accepted.connect(do_save)
            bb.rejected.connect(d.reject)
            d.exec_()
            return
        if self.instructorTable.hasFocus():
            r = self.instructorTable.currentRow()
            if r < 0:
                return
            iid = self.instructorTable.item(r, 0).text()
            target = None
            
            
            
            
            
            
            
            for ins in instructors:
                if ins.instructor_id == iid:
                    target = ins
            if target is None:
                return
            d = QtWidgets.QDialog(self)
            d.setWindowTitle("Edit Instructor")
            fl = QtWidgets.QFormLayout(d)
            nEdit = QtWidgets.QLineEdit(target.name)
            aEdit = QtWidgets.QLineEdit(str(target.age))
            eEdit = QtWidgets.QLineEdit(target._email)
            iEdit = QtWidgets.QLineEdit(target.instructor_id)
            fl.addRow("Name", nEdit)
            fl.addRow("Age", aEdit)
            fl.addRow("Email", eEdit)
            fl.addRow("Instructor ID", iEdit)
            bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
            fl.addRow(bb)
            def do_save():
                newName = nEdit.text().strip()
                newAge = aEdit.text().strip()
                newEmail = eEdit.text().strip()
                
                
                
                
                
                
                
                
                newId = iEdit.text().strip()
                if newName == "" or newAge == "" or newEmail == "" or newId == "":
                    return
                if not is_valid_age(newAge):
                    return
                if not is_valid_email(newEmail):
                    return
                ok = db_update_instructor(target.instructor_id, newName, newAge, newEmail, newId)
                if not ok:
                    return
                reload_from_db()
                self.refresh_views()
                d.accept()
            bb.accepted.connect(do_save)
            bb.rejected.connect(d.reject)
            d.exec_()
            return
        if self.courseTable.hasFocus():
            r = self.courseTable.currentRow()
            
            
            
            
            
            
            
            
            if r < 0:
                return
            cid = self.courseTable.item(r, 0).text()
            target = None
            for c in courses:
                if c.course_id == cid:
                    target = c
            if target is None:
                return
            d = QtWidgets.QDialog(self)
            d.setWindowTitle("Edit Course")
            fl = QtWidgets.QFormLayout(d)
            idEdit = QtWidgets.QLineEdit(target.course_id)
            nameEdit = QtWidgets.QLineEdit(target.course_name)
            insEdit = QtWidgets.QComboBox()
            for ins in instructors:
                insEdit.addItem(ins.instructor_id)
            if target.instructor:
                idx = insEdit.findText(target.instructor.instructor_id)
                if idx >= 0:
                    insEdit.setCurrentIndex(idx)
            fl.addRow("Course ID", idEdit)
            fl.addRow("Course Name", nameEdit)
            fl.addRow("Instructor ID", insEdit)
            
            
            
            
            
            
            
            
            
            
            
            
            bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
            fl.addRow(bb)
            def do_save():
                newCid = idEdit.text().strip()
                newName = nameEdit.text().strip()
                newInsId = insEdit.currentText().strip()
                if newCid == "" or newName == "" or newInsId == "":
                    return
                ok = db_update_course(target.course_id, newCid, newName, newInsId)
                if not ok:
                    return
                
                
                
                
                
                
                
                
                
                
                reload_from_db()
                self.refresh_views()
                d.accept()
            bb.accepted.connect(do_save)
            bb.rejected.connect(d.reject)
            d.exec_()

    def delete_selected_qt(self):
        if self.studentTable.hasFocus():
            r = self.studentTable.currentRow()
            if r < 0:
                
                return
            sid = self.studentTable.item(r, 0).text()
            db_delete_student(sid)
            reload_from_db()
            self.refresh_views()
            return
        if self.instructorTable.hasFocus():
            r = self.instructorTable.currentRow()
            if r < 0:
                return
            iid = self.instructorTable.item(r, 0).text()
            db_delete_instructor(iid)
            reload_from_db()
            self.refresh_views()
            return
        
        if self.courseTable.hasFocus():
            r = self.courseTable.currentRow()
            if r < 0:
                return
            cid = self.courseTable.item(r, 0).text()
            db_delete_course(cid)
            reload_from_db()
            self.refresh_views()

    def save_now(self):
        try:
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Saved", "Database saved")
        except:
            QtWidgets.QMessageBox.critical(self, "Error", "Save failed")

    def load_now(self):
        try:
            reload_from_db()
            self.refresh_views()
            QtWidgets.QMessageBox.information(self, "Loaded", "Data loaded from DB")
        except:
            
            QtWidgets.QMessageBox.critical(self, "Error", "Load failed")

    def backup_now(self):
        try:
            name = backup_db()
            QtWidgets.QMessageBox.information(self, "Backup", name)
        except:
            QtWidgets.QMessageBox.critical(self, "Error", "Backup failed")

