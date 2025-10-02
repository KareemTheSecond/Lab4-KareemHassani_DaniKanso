
"""Tkinter GUI for the School Management System.

Provides a tabbed interface to manage students, instructors, and courses with
JSON/CSV import-export and SQLite synchronization.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models import School, Student, Instructor, Course
from storage import save_json, load_json, export_csv, school_to_db, db_to_school, backup_db, init_db

class SchoolAppTk:
    """Tkinter application window for managing school data.

    Provides tabs for Students, Instructors, and Courses, plus search,
    JSON/CSV operations, and SQLite synchronization.
    """
    def __init__(self, root):
        """Constructor.

        Initializes the model and database, builds the UI, and refreshes tables.

        :param root: Tk root window.
        :type root: tk.Tk
        """
        self.root = root
        self.root.title("School Management System (Tkinter)")
        self.school = School()
        init_db()

        self._build_ui()
        self._refresh_all_tables()

    def _build_ui(self):
        """Create the search bar, action buttons, and tabbed views."""
        # Search bar
        search_frame = ttk.Frame(self.root, padding=6)
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side="left", expand=True, fill="x", padx=6)
        ttk.Button(search_frame, text="Go", command=self._on_search).pack(side="left")
        ttk.Button(search_frame, text="Clear", command=self._on_clear_search).pack(side="left", padx=4)

        # Buttons
        btns = ttk.Frame(self.root, padding=(6,0,6,6))
        btns.pack(fill="x")
        ttk.Button(btns, text="Save JSON", command=self._save_json).pack(side="left")
        ttk.Button(btns, text="Load JSON", command=self._load_json).pack(side="left", padx=4)
        ttk.Button(btns, text="Export CSV", command=self._export_csv).pack(side="left")
        ttk.Button(btns, text="Sync → DB", command=self._sync_to_db).pack(side="left", padx=4)
        ttk.Button(btns, text="Load ← DB", command=self._load_from_db).pack(side="left")
        ttk.Button(btns, text="Backup DB", command=self._backup_db).pack(side="left", padx=4)

        # Notebook
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(expand=True, fill="both")

        self._build_students_tab()
        self._build_instructors_tab()
        self._build_courses_tab()

    # --------- Students Tab ---------
    def _build_students_tab(self):
        """Create the Students tab (form + table)."""
        tab = ttk.Frame(self.nb, padding=6)
        self.nb.add(tab, text="Students")

        form = ttk.LabelFrame(tab, text="Add / Edit Student")
        form.pack(fill="x")
        self.stu_id = tk.StringVar()
        self.stu_name = tk.StringVar()
        self.stu_age = tk.StringVar()
        self.stu_email = tk.StringVar()
        for i,(lbl,var) in enumerate([("ID",self.stu_id),("Name",self.stu_name),("Age",self.stu_age),("Email",self.stu_email)]):
            ttk.Label(form, text=lbl).grid(row=i, column=0, sticky="w", padx=4, pady=2)
            ttk.Entry(form, textvariable=var).grid(row=i, column=1, sticky="ew", padx=4, pady=2)
        form.columnconfigure(1, weight=1)
        btns = ttk.Frame(form); btns.grid(row=0,column=2,rowspan=4, padx=6)
        ttk.Button(btns, text="Add / Update", command=self._add_update_student).pack(fill="x")
        ttk.Button(btns, text="Delete", command=self._delete_student).pack(fill="x", pady=4)

        # Table
        self.stu_tv = ttk.Treeview(tab, columns=("id","name","age","email","courses"), show="headings", height=8)
        for c, w in zip(("id","name","age","email","courses"), (100,160,60,180,240)):
            self.stu_tv.heading(c, text=c.title())
            self.stu_tv.column(c, width=w, anchor="w")
        self.stu_tv.pack(expand=True, fill="both", pady=(6,0))
        self.stu_tv.bind("<<TreeviewSelect>>", self._on_student_select)

    def _add_update_student(self):
        """Create or update a student from the form values.

        :raises ValueError: When required fields are missing or invalid.
        """
        try:
            s = Student(
                student_id=self.stu_id.get().strip(),
                name=self.stu_name.get().strip(),
                age=int(self.stu_age.get().strip() or "0"),
                _email=self.stu_email.get().strip()
            )
            if not s.student_id:
                raise ValueError("Student ID is required")
            if s.student_id in self.school.students:
                self.school.update_student(s.student_id, name=s.name, age=s.age, _email=s._email)
            else:
                self.school.add_student(s)
            self._refresh_students()
            self._update_dropdowns()
            self._clear_student_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_student(self):
        """Delete the selected student from the model and refresh views."""
        item = self._selected_item(self.stu_tv)
        if not item: return
        sid = self.stu_tv.set(item, "id")
        self.school.delete_student(sid)
        self._refresh_students()
        self._update_dropdowns()

    def _on_student_select(self, _ev=None):
        """Populate the student form on table selection."""
        item = self._selected_item(self.stu_tv)
        if not item: return
        self.stu_id.set(self.stu_tv.set(item, "id"))
        self.stu_name.set(self.stu_tv.set(item, "name"))
        self.stu_age.set(self.stu_tv.set(item, "age"))
        self.stu_email.set(self.stu_tv.set(item, "email"))

    def _refresh_students(self, results=None):
        """Reload students table with optional filtered list."""
        self._refresh_table(self.stu_tv)
        data = results or list(self.school.students.values())
        for s in data:
            self.stu_tv.insert("", "end", values=(s.student_id, s.name, s.age, s._email, ",".join(s.registered_courses)))

    def _clear_student_form(self):
        """Clear all student form input fields."""
        for v in (self.stu_id, self.stu_name, self.stu_age, self.stu_email):
            v.set("")

    # --------- Instructors Tab ---------
    def _build_instructors_tab(self):
        """Create the Instructors tab (form + table)."""
        tab = ttk.Frame(self.nb, padding=6)
        self.nb.add(tab, text="Instructors")

        form = ttk.LabelFrame(tab, text="Add / Edit Instructor")
        form.pack(fill="x")
        self.ins_id = tk.StringVar()
        self.ins_name = tk.StringVar()
        self.ins_age = tk.StringVar()
        self.ins_email = tk.StringVar()
        for i,(lbl,var) in enumerate([("ID",self.ins_id),("Name",self.ins_name),("Age",self.ins_age),("Email",self.ins_email)]):
            ttk.Label(form, text=lbl).grid(row=i, column=0, sticky="w", padx=4, pady=2)
            ttk.Entry(form, textvariable=var).grid(row=i, column=1, sticky="ew", padx=4, pady=2)
        form.columnconfigure(1, weight=1)
        btns = ttk.Frame(form); btns.grid(row=0,column=2,rowspan=4, padx=6)
        ttk.Button(btns, text="Add / Update", command=self._add_update_instructor).pack(fill="x")
        ttk.Button(btns, text="Delete", command=self._delete_instructor).pack(fill="x", pady=4)

        self.ins_tv = ttk.Treeview(tab, columns=("id","name","age","email","courses"), show="headings", height=8)
        for c, w in zip(("id","name","age","email","courses"), (100,160,60,180,240)):
            self.ins_tv.heading(c, text=c.title())
            self.ins_tv.column(c, width=w, anchor="w")
        self.ins_tv.pack(expand=True, fill="both", pady=(6,0))
        self.ins_tv.bind("<<TreeviewSelect>>", self._on_instructor_select)

    def _add_update_instructor(self):
        """Create or update an instructor from the form values.

        :raises ValueError: When required fields are missing or invalid.
        """
        try:
            i = Instructor(
                instructor_id=self.ins_id.get().strip(),
                name=self.ins_name.get().strip(),
                age=int(self.ins_age.get().strip() or "0"),
                _email=self.ins_email.get().strip()
            )
            if not i.instructor_id:
                raise ValueError("Instructor ID is required")
            if i.instructor_id in self.school.instructors:
                self.school.update_instructor(i.instructor_id, name=i.name, age=i.age, _email=i._email)
            else:
                self.school.add_instructor(i)
            self._refresh_instructors()
            self._update_dropdowns()
            self._clear_instructor_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_instructor(self):
        """Delete the selected instructor from the model and refresh views."""
        item = self._selected_item(self.ins_tv)
        if not item: return
        iid = self.ins_tv.set(item, "id")
        self.school.delete_instructor(iid)
        self._refresh_instructors()
        self._update_dropdowns()

    def _on_instructor_select(self, _ev=None):
        """Populate the instructor form on table selection."""
        item = self._selected_item(self.ins_tv)
        if not item: return
        self.ins_id.set(self.ins_tv.set(item, "id"))
        self.ins_name.set(self.ins_tv.set(item, "name"))
        self.ins_age.set(self.ins_tv.set(item, "age"))
        self.ins_email.set(self.ins_tv.set(item, "email"))

    def _refresh_instructors(self, results=None):
        """Reload instructors table with optional filtered list."""
        self._refresh_table(self.ins_tv)
        data = results or list(self.school.instructors.values())
        for i in data:
            self.ins_tv.insert("", "end", values=(i.instructor_id, i.name, i.age, i._email, ",".join(i.assigned_courses)))

    def _clear_instructor_form(self):
        """Clear all instructor form input fields."""
        for v in (self.ins_id, self.ins_name, self.ins_age, self.ins_email):
            v.set("")

    # --------- Courses Tab ---------
    def _build_courses_tab(self):
        """Create the Courses tab (form, relationships, and table)."""
        tab = ttk.Frame(self.nb, padding=6)
        self.nb.add(tab, text="Courses")

        form = ttk.LabelFrame(tab, text="Add / Edit Course")
        form.pack(fill="x")
        self.c_id = tk.StringVar()
        self.c_name = tk.StringVar()
        self.c_instructor = tk.StringVar()
        for i,(lbl,var) in enumerate([("Course ID",self.c_id),("Course Name",self.c_name),("Instructor ID",self.c_instructor)]):
            ttk.Label(form, text=lbl).grid(row=i, column=0, sticky="w", padx=4, pady=2)
            ttk.Entry(form, textvariable=var).grid(row=i, column=1, sticky="ew", padx=4, pady=2)
        form.columnconfigure(1, weight=1)
        btns = ttk.Frame(form); btns.grid(row=0,column=2,rowspan=3, padx=6)
        ttk.Button(btns, text="Add / Update", command=self._add_update_course).pack(fill="x")
        ttk.Button(btns, text="Delete", command=self._delete_course).pack(fill="x", pady=4)

        # Register/Assign subframe
        relf = ttk.LabelFrame(tab, text="Relationships")
        relf.pack(fill="x", pady=6)
        self.reg_student = tk.StringVar()
        self.reg_course = tk.StringVar()
        ttk.Label(relf, text="Student ID").grid(row=0,column=0, padx=4, pady=2)
        self.reg_student_combo = ttk.Combobox(relf, textvariable=self.reg_student, state="readonly")
        self.reg_student_combo.grid(row=0,column=1, padx=4, pady=2)
        ttk.Label(relf, text="→ Course ID").grid(row=0,column=2)
        self.reg_course_combo = ttk.Combobox(relf, textvariable=self.reg_course, state="readonly")
        self.reg_course_combo.grid(row=0,column=3, padx=4, pady=2)
        ttk.Button(relf, text="Register", command=self._register_student).grid(row=0,column=4, padx=6)

        self.assign_instructor_id = tk.StringVar()
        self.assign_course_id = tk.StringVar()
        ttk.Label(relf, text="Instructor ID").grid(row=1,column=0, padx=4, pady=2)
        self.assign_instructor_combo = ttk.Combobox(relf, textvariable=self.assign_instructor_id, state="readonly")
        self.assign_instructor_combo.grid(row=1,column=1, padx=4, pady=2)
        ttk.Label(relf, text="→ Course ID").grid(row=1,column=2)
        self.assign_course_combo = ttk.Combobox(relf, textvariable=self.assign_course_id, state="readonly")
        self.assign_course_combo.grid(row=1,column=3, padx=4, pady=2)
        ttk.Button(relf, text="Assign", command=self._assign_instructor).grid(row=1,column=4, padx=6)

        # Table
        self.c_tv = ttk.Treeview(tab, columns=("id","name","instructor","students"), show="headings", height=10)
        for c, w in zip(("id","name","instructor","students"), (100,200,120,320)):
            self.c_tv.heading(c, text=c.title())
            self.c_tv.column(c, width=w, anchor="w")
        self.c_tv.pack(expand=True, fill="both", pady=(6,0))
        self.c_tv.bind("<<TreeviewSelect>>", self._on_course_select)

    def _add_update_course(self):
        """Create or update a course from the form values.

        :raises ValueError: When required fields are missing or invalid.
        """
        try:
            c = Course(
                course_id=self.c_id.get().strip(),
                course_name=self.c_name.get().strip(),
                instructor_id=(self.c_instructor.get().strip() or None)
            )
            if not c.course_id:
                raise ValueError("Course ID is required")
            if c.course_id in self.school.courses:
                self.school.update_course(c.course_id, course_name=c.course_name, instructor_id=c.instructor_id)
            else:
                self.school.add_course(c)
            self._refresh_courses()
            self._update_dropdowns()
            self._clear_course_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_course(self):
        """Delete the selected course from the model and refresh views."""
        item = self._selected_item(self.c_tv)
        if not item: return
        cid = self.c_tv.set(item, "id")
        self.school.delete_course(cid)
        self._refresh_courses()
        self._update_dropdowns()

    def _on_course_select(self, _ev=None):
        """Populate the course form on table selection."""
        item = self._selected_item(self.c_tv)
        if not item: return
        self.c_id.set(self.c_tv.set(item, "id"))
        self.c_name.set(self.c_tv.set(item, "name"))
        self.c_instructor.set(self.c_tv.set(item, "instructor"))

    def _register_student(self):
        """Register the selected student into the selected course."""
        try:
            sid = self.reg_student.get().strip()
            cid = self.reg_course.get().strip()
            self.school.register_student_in_course(sid, cid)
            self._refresh_students(); self._refresh_courses()
            self._update_dropdowns()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _assign_instructor(self):
        """Assign the selected instructor to the selected course."""
        try:
            iid = self.assign_instructor_id.get().strip()
            cid = self.assign_course_id.get().strip()
            self.school.assign_instructor_to_course(iid, cid)
            self._refresh_instructors(); self._refresh_courses()
            self._update_dropdowns()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --------- Helpers ---------
    def _selected_item(self, tv):
        """Return the selected Treeview item id or None if no selection.

        :param tv: Treeview instance to inspect.
        :type tv: ttk.Treeview
        :return: Selected item id or None.
        :rtype: str | None
        """
        sel = tv.selection()
        return sel[0] if sel else None

    def _refresh_table(self, tv):
        """Remove all rows from the provided Treeview widget.

        :param tv: Treeview to clear.
        :type tv: ttk.Treeview
        """
        for x in tv.get_children():
            tv.delete(x)

    def _refresh_courses(self, results=None):
        """Reload courses table with optional filtered list.

        :param results: Optional list of courses to show.
        :type results: list[Course] | None
        """
        self._refresh_table(self.c_tv)
        data = results or list(self.school.courses.values())
        for c in data:
            self.c_tv.insert("", "end", values=(c.course_id, c.course_name, c.instructor_id or "", ",".join(c.enrolled_students)))

    def _refresh_all_tables(self):
        """Refresh all entity tables and update dropdowns."""
        self._refresh_students()
        self._refresh_instructors()
        self._refresh_courses()
        self._update_dropdowns()

    def _update_dropdowns(self):
        """Update combobox options for students, instructors, and courses."""
        # Update student dropdown
        student_ids = list(self.school.students.keys())
        self.reg_student_combo['values'] = student_ids
        
        # Update instructor dropdown  
        instructor_ids = list(self.school.instructors.keys())
        self.assign_instructor_combo['values'] = instructor_ids
        
        # Update course dropdowns
        course_ids = list(self.school.courses.keys())
        self.reg_course_combo['values'] = course_ids
        self.assign_course_combo['values'] = course_ids

    # --------- Search ---------
    def _on_search(self):
        """Execute a contains-based search and filter all three tables."""
        text = self.search_var.get()
        res = self.school.search(text)
        self._refresh_students(res["students"])
        self._refresh_instructors(res["instructors"])
        self._refresh_courses(res["courses"])

    def _on_clear_search(self):
        """Clear the search field and restore full results in all tables."""
        self.search_var.set("")
        self._refresh_all_tables()

    # --------- File ops ---------
    def _save_json(self):
        """Prompt for a JSON path and save the current model to it."""
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not path: return
        save_json(self.school, path)
        messagebox.showinfo("Saved", f"Data saved to {path}")

    def _load_json(self):
        """Prompt for a JSON path and load it into the model and UI."""
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not path: return
        self.school = load_json(path)
        self._refresh_all_tables()

    def _export_csv(self):
        """Prompt for a folder and export CSV files for all entities."""
        folder = filedialog.askdirectory()
        if not folder: return
        export_csv(self.school, folder)
        messagebox.showinfo("Exported", f"CSV files exported to {folder}")

    def _sync_to_db(self):
        """Synchronize the current model to the SQLite database."""
        school_to_db(self.school)
        messagebox.showinfo("Database", "Synchronized to SQLite database")

    def _load_from_db(self):
        """Load data from SQLite into the model and refresh the UI."""
        self.school = db_to_school()
        self._refresh_all_tables()
        messagebox.showinfo("Database", "Loaded from SQLite database")

    def _backup_db(self):
        """Prompt for a folder and back up the database file into it."""
        folder = filedialog.askdirectory()
        if not folder: return
        path = backup_db(folder)
        messagebox.showinfo("Backup", f"Database backed up to {path}")

def main():
    """Entry point to launch the Tkinter app."""
    root = tk.Tk()
    app = SchoolAppTk(root)
    root.mainloop()

if __name__ == "__main__":
    main()
