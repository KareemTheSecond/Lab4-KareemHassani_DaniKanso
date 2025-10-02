# Lab4-KareemHassani_DaniKanso
# School Management Mini App

Two UIs for the same school data:

- **PyQt5 app** (desktop-style): `main.py` + `pyqt_core.py`  
- **Tkinter app** (lightweight): `app_tkinter.py`

Both work with the same SQLite database: `school.db`, and support JSON/CSV import–export.

---

## Features
- Manage **Students**, **Instructors**, **Courses** (add / update / delete)
- **Register** students to courses
- **Assign** instructors to courses
- **Import/Export** data (JSON & CSV)
- **SQLite** persistence with auto-init and **backup**

---

## Requirements
- Python 3.9+
- For **PyQt5 app**: `pip install PyQt5`  
- Tkinter usually ships with Python (on some Linux distros you may need `python3-tk`)

---

## How to Run

### Option A — PyQt5 app (main desktop UI)
```bash
python main.py
```

### Option B — Tkinter app (alternate UI)
```bash
python app_tkinter.py
```

---

## Project Layout
```
main.py                # Launches PyQt5 app
pyqt_core.py           # PyQt5 MainWindow + DB/CSV actions
app_tkinter.py         # Tkinter app with tabs and import/export
models.py              # Dataclasses: School, Student, Instructor, Course
storage.py             # JSON/CSV/SQLite persistence helpers
utils.py               # Validation helpers (email, non-negative int)
school.db              # SQLite database
```

---

## Data & Persistence
- The database is initialized automatically if it doesn’t exist (`init_db`).
- Export/import JSON or CSV from either UI.
- Use the **backup** action to copy `school.db` to a timestamped file.

---

## Notes
- `main.py` runs the **PyQt5** interface.  
- `app_tkinter.py` runs the **Tkinter** interface.  
- Both UIs manage the same data model and database.
