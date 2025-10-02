
"""Data models for the School Management System.

Contains core entities (Person, Student, Instructor, Course) and the main
School class that manages collections and relationships between them.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from utils import is_valid_email, non_negative_int

@dataclass
class Person:
    """Base class for people in the school system.
    
    Provides common fields (name, age, email) and validation for all person types.
    
    :param name: Full name of the person.
    :type name: str
    :param age: Age in years.
    :type age: int
    :param _email: Email address (private field, use email property).
    :type _email: str
    """
    name: str
    age: int
    _email: str = field(repr=False, default="")

    def introduce(self) -> str:
        """Return a friendly introduction string.
        
        :return: Formatted introduction with name, age, and email.
        :rtype: str
        """
        return f"Hi, I'm {self.name}, {self.age} years old. You can reach me at {self.email}."

    @property
    def email(self) -> str:
        """Get the email address.
        
        :return: Email address.
        :rtype: str
        """
        return self._email

    @email.setter
    def email(self, value: str):
        """Set the email address with validation.
        
        :param value: New email address.
        :type value: str
        :raises ValueError: If email format is invalid.
        """
        if not is_valid_email(value):
            raise ValueError("Invalid email format")
        self._email = value

    def validate(self):
        """Validate all person fields.
        
        :raises ValueError: If any field is invalid (empty name, negative age, bad email).
        """
        if not self.name.strip():
            raise ValueError("Name is required")
        if not non_negative_int(self.age):
            raise ValueError("Age must be a non-negative integer")
        if not is_valid_email(self._email):
            raise ValueError("Invalid email format")

@dataclass
class Course:
    """Represents a course in the school system.
    
    :param course_id: Unique identifier for the course.
    :type course_id: str
    :param course_name: Human-readable course name.
    :type course_name: str
    :param instructor_id: ID of assigned instructor (optional).
    :type instructor_id: str | None
    :param enrolled_students: List of student IDs enrolled in this course.
    :type enrolled_students: list[str]
    """
    course_id: str
    course_name: str
    instructor_id: Optional[str] = None
    enrolled_students: List[str] = field(default_factory=list)

    def add_student(self, student_id: str):
        """Add a student to this course if not already enrolled.
        
        :param student_id: ID of the student to enroll.
        :type student_id: str
        """
        if student_id not in self.enrolled_students:
            self.enrolled_students.append(student_id)

@dataclass
class Student(Person):
    """A student in the school system.
    
    Inherits person fields (name, age, email) and adds student-specific data.
    
    :param student_id: Unique student identifier.
    :type student_id: str
    :param registered_courses: List of course IDs the student is enrolled in.
    :type registered_courses: list[str]
    """
    student_id: str = ""
    registered_courses: List[str] = field(default_factory=list)

    def register_course(self, course_id: str):
        """Register this student for a course if not already registered.
        
        :param course_id: ID of the course to register for.
        :type course_id: str
        """
        if course_id not in self.registered_courses:
            self.registered_courses.append(course_id)

@dataclass
class Instructor(Person):
    """An instructor in the school system.
    
    Inherits person fields (name, age, email) and adds instructor-specific data.
    
    :param instructor_id: Unique instructor identifier.
    :type instructor_id: str
    :param assigned_courses: List of course IDs this instructor teaches.
    :type assigned_courses: list[str]
    """
    instructor_id: str = ""
    assigned_courses: List[str] = field(default_factory=list)

    def assign_course(self, course_id: str):
        """Assign this instructor to teach a course if not already assigned.
        
        :param course_id: ID of the course to assign.
        :type course_id: str
        """
        if course_id not in self.assigned_courses:
            self.assigned_courses.append(course_id)

class School:
    """Central data model managing students, instructors, and courses.
    
    Provides CRUD operations, relationship management, search functionality,
    and serialization to/from dictionaries for JSON/database persistence.
    
    :ivar students: Dictionary mapping student IDs to Student objects.
    :vartype students: dict[str, Student]
    :ivar instructors: Dictionary mapping instructor IDs to Instructor objects.
    :vartype instructors: dict[str, Instructor]
    :ivar courses: Dictionary mapping course IDs to Course objects.
    :vartype courses: dict[str, Course]
    """
    def __init__(self):
        """Initialize empty collections for all entity types."""
        self.students: Dict[str, Student] = {}
        self.instructors: Dict[str, Instructor] = {}
        self.courses: Dict[str, Course] = {}

    # ---------- CRUD: Students ----------
    def add_student(self, s: Student):
        """Add a new student to the school.
        
        :param s: Student object to add.
        :type s: Student
        :raises ValueError: If student data is invalid or ID is missing.
        """
        s.validate()
        if not s.student_id:
            raise ValueError("student_id is required")
        self.students[s.student_id] = s

    def update_student(self, student_id: str, **updates):
        """Update an existing student's fields.
        
        :param student_id: ID of student to update.
        :type student_id: str
        :param updates: Field names and new values.
        :raises KeyError: If student ID not found.
        :raises ValueError: If updated data is invalid.
        """
        s = self.students[student_id]
        for k,v in updates.items():
            setattr(s, k, v)
        s.validate()

    def delete_student(self, student_id: str):
        """Remove a student and all their course enrollments.
        
        :param student_id: ID of student to delete.
        :type student_id: str
        """
        self.students.pop(student_id, None)
        # remove from courses
        for c in self.courses.values():
            if student_id in c.enrolled_students:
                c.enrolled_students.remove(student_id)

    # ---------- CRUD: Instructors ----------
    def add_instructor(self, ins: Instructor):
        ins.validate()
        if not ins.instructor_id:
            raise ValueError("instructor_id is required")
        self.instructors[ins.instructor_id] = ins

    def update_instructor(self, instructor_id: str, **updates):
        i = self.instructors[instructor_id]
        for k,v in updates.items():
            setattr(i, k, v)
        i.validate()

    def delete_instructor(self, instructor_id: str):
        self.instructors.pop(instructor_id, None)
        # unassign in courses
        for c in self.courses.values():
            if c.instructor_id == instructor_id:
                c.instructor_id = None

    # ---------- CRUD: Courses ----------
    def add_course(self, c: Course):
        if not c.course_id.strip():
            raise ValueError("course_id is required")
        if not c.course_name.strip():
            raise ValueError("course_name is required")
        self.courses[c.course_id] = c

    def update_course(self, course_id: str, **updates):
        c = self.courses[course_id]
        for k,v in updates.items():
            setattr(c, k, v)

    def delete_course(self, course_id: str):
        self.courses.pop(course_id, None)
        # remove from student registrations
        for s in self.students.values():
            if course_id in s.registered_courses:
                s.registered_courses.remove(course_id)

    # ---------- Relationships ----------
    def register_student_in_course(self, student_id: str, course_id: str):
        s = self.students[student_id]
        c = self.courses[course_id]
        s.register_course(course_id)
        c.add_student(student_id)

    def assign_instructor_to_course(self, instructor_id: str, course_id: str):
        i = self.instructors[instructor_id]
        c = self.courses[course_id]
        i.assign_course(course_id)
        c.instructor_id = instructor_id

    # ---------- Search ----------
    def search(self, text: str):
        """Search for entities containing the given text.
        
        Searches names and IDs of students, instructors, and courses.
        If text is empty, returns all entities.
        
        :param text: Search term (case-insensitive).
        :type text: str
        :return: Dictionary with lists of matching students, instructors, courses.
        :rtype: dict[str, list]
        """
        text = (text or "").lower().strip()
        results = {"students": [], "instructors": [], "courses": []}
        if not text:
            results["students"] = list(self.students.values())
            results["instructors"] = list(self.instructors.values())
            results["courses"] = list(self.courses.values())
            return results

        for s in self.students.values():
            if text in s.name.lower() or text in s.student_id.lower():
                results["students"].append(s)
        for i in self.instructors.values():
            if text in i.name.lower() or text in i.instructor_id.lower():
                results["instructors"].append(i)
        for c in self.courses.values():
            if (text in c.course_id.lower() or 
                text in c.course_name.lower() or
                (c.instructor_id and text in c.instructor_id.lower())):
                results["courses"].append(c)
        return results

    # ---------- Serialization ----------
    def to_dict(self) -> dict:
        return {
            "students": [asdict(s) for s in self.students.values()],
            "instructors": [asdict(i) for i in self.instructors.values()],
            "courses": [asdict(c) for c in self.courses.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "School":
        sc = cls()
        for s in data.get("students", []):
            st = Student(**{k:v for k,v in s.items() if k in {"name","age","_email","student_id","registered_courses"}})
            sc.students[st.student_id] = st
        for i in data.get("instructors", []):
            ins = Instructor(**{k:v for k,v in i.items() if k in {"name","age","_email","instructor_id","assigned_courses"}})
            sc.instructors[ins.instructor_id] = ins
        for c in data.get("courses", []):
            co = Course(**{k:v for k,v in c.items() if k in {"course_id","course_name","instructor_id","enrolled_students"}})
            sc.courses[co.course_id] = co
        return sc
