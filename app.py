import tkinter as tk
from tkinter import ttk, messagebox
import Core_Tinker_models as core


core.init_db(core.dbPath)
core.reload_from_db()
