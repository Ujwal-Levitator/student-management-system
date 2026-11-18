import csv
import os
import pickle
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


CLASS_OPTIONS = tuple(str(class_number) for class_number in range(1, 13))
SECTION_OPTIONS = ("A", "B", "C", "D")
CSV_COLUMNS = (
    "record_type",
    "roll_no",
    "name",
    "age",
    "address",
    "parent_name",
    "parent_phone",
    "previous_result",
    "test_marks",
    "class_name",
    "section",
    "next_roll_no",
)


class Student:
    def __init__(
        self,
        roll_no,
        name,
        age,
        address,
        parent_name,
        parent_phone,
        previous_result,
        test_marks,
        class_name="",
        section="",
    ):
        self.roll_no = roll_no
        self.name = name
        self.age = age
        self.address = address
        self.parent_name = parent_name
        self.parent_phone = parent_phone
        self.previous_result = previous_result
        self.test_marks = test_marks
        self.class_name = class_name
        self.section = section


class _StudentUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module in ("__main__", "student_system") and name == "Student":
            return Student
        raise pickle.UnpicklingError(
            "The legacy student file contains an unsupported object."
        )


class Classroom:
    def __init__(self, data_file=None):
        self.data_file = Path(data_file) if data_file else Path(__file__).with_name(
            "student_details.csv"
        )
        self.legacy_data_file = self.data_file.with_suffix(".dat")
        self.students = []
        self._students_by_roll = {}
        self.next_roll_no = 1
        self.load_details()

    def add_student(self, student):
        if student.roll_no in self._students_by_roll:
            raise ValueError("A student with this roll number already exists.")

        self.students.append(student)
        self._students_by_roll[student.roll_no] = student
        old_next_roll_no = self.next_roll_no
        self.next_roll_no = max(self.next_roll_no, student.roll_no + 1)
        try:
            self.save_details()
        except Exception:
            self.students.pop()
            del self._students_by_roll[student.roll_no]
            self.next_roll_no = old_next_roll_no
            raise

    def get_student(self, roll_no):
        return self._students_by_roll.get(roll_no)

    def get_classroom_counts(self):
        counts = {}
        for student in self.students:
            classroom = (
                getattr(student, "class_name", "") or "",
                getattr(student, "section", "") or "",
            )
            counts[classroom] = counts.get(classroom, 0) + 1

        def sort_key(item):
            class_name, section = item[0]
            if not class_name:
                return (1, 0, "", section.casefold())
            if class_name.isdigit():
                return (0, 0, int(class_name), section.casefold())
            return (0, 1, class_name.casefold(), section.casefold())

        return dict(
            sorted(counts.items(), key=sort_key)
        )

    def get_students_for_classroom(self, class_name, section):
        return [
            student
            for student in self.students
            if (
                getattr(student, "class_name", "") or "",
                getattr(student, "section", "") or "",
            )
            == (class_name, section)
        ]

    def update_student(self, student):
        existing_student = self._students_by_roll.get(student.roll_no)
        if existing_student is None:
            return False

        student_index = self.students.index(existing_student)
        self.students[student_index] = student
        self._students_by_roll[student.roll_no] = student
        try:
            self.save_details()
        except Exception:
            self.students[student_index] = existing_student
            self._students_by_roll[student.roll_no] = existing_student
            raise
        return True

    def remove_student(self, roll_no):
        student = self._students_by_roll.get(roll_no)
        if student is None:
            return False

        self.students.remove(student)
        del self._students_by_roll[roll_no]
        try:
            self.save_details()
        except Exception:
            self.students.append(student)
            self._students_by_roll[roll_no] = student
            raise
        return True

    def save_details(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=str(self.data_file.parent),
                prefix=self.data_file.name + ".",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    {"record_type": "metadata", "next_roll_no": self.next_roll_no}
                )
                for student in self.students:
                    writer.writerow(
                        {
                            "record_type": "student",
                            "roll_no": student.roll_no,
                            "name": student.name,
                            "age": student.age,
                            "address": student.address,
                            "parent_name": student.parent_name,
                            "parent_phone": student.parent_phone,
                            "previous_result": student.previous_result,
                            "test_marks": student.test_marks,
                            "class_name": getattr(student, "class_name", ""),
                            "section": getattr(student, "section", ""),
                        }
                    )
            os.replace(str(temporary_path), str(self.data_file))
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def load_details(self):
        if self.data_file.exists():
            self._load_csv()
            return
        if not self.legacy_data_file.exists():
            return

        self._load_legacy_data()
        self.save_details()

    def _load_csv(self):
        try:
            with self.data_file.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames is None or not set(CSV_COLUMNS).issubset(
                    reader.fieldnames
                ):
                    raise ValueError("The CSV student data file has an invalid header.")

                students = []
                saved_next_roll_no = 1
                metadata_found = False
                for row in reader:
                    if not row or not any(value for value in row.values()):
                        continue
                    if row["record_type"] == "metadata":
                        if metadata_found:
                            raise ValueError(
                                "The CSV student data file contains duplicate metadata."
                            )
                        metadata_found = True
                        try:
                            saved_next_roll_no = int(row["next_roll_no"])
                        except (TypeError, ValueError) as error:
                            raise ValueError(
                                "The CSV student data file has an invalid next roll number."
                            ) from error
                        continue
                    if row["record_type"] != "student":
                        raise ValueError(
                            "The CSV student data file contains an unknown record type."
                        )
                    student_columns = CSV_COLUMNS[1:-1]
                    if any(row[column] is None for column in student_columns):
                        raise ValueError(
                            "Incomplete student record on CSV line {}.".format(
                                reader.line_num
                            )
                        )

                    try:
                        students.append(
                            Student(
                                int(row["roll_no"]),
                                row["name"],
                                int(row["age"]),
                                row["address"],
                                row["parent_name"],
                                row["parent_phone"],
                                row["previous_result"],
                                row["test_marks"],
                                row.get("class_name") or "",
                                row.get("section") or "",
                            )
                        )
                    except (KeyError, TypeError, ValueError) as error:
                        raise ValueError(
                            "Invalid student record on CSV line {}.".format(
                                reader.line_num
                            )
                        ) from error
        except csv.Error as error:
            raise ValueError("The CSV student data file could not be parsed.") from error

        self._set_students(students, saved_next_roll_no)

    def _load_legacy_data(self):
        try:
            with self.legacy_data_file.open("rb") as file:
                data = _StudentUnpickler(file).load()
        except EOFError:
            raise ValueError("The legacy student data file is empty.")

        if not isinstance(data, dict) or not isinstance(data.get("students"), list):
            raise ValueError("The legacy student data file has an invalid format.")
        self._set_students(data["students"], data.get("next_roll_no", 1))

    def _set_students(self, students, saved_next_roll_no):
        student_index = {}
        for student in students:
            if not isinstance(student, Student):
                raise ValueError("The student data file contains an invalid record.")
            if not isinstance(student.roll_no, int) or student.roll_no < 1:
                raise ValueError("Student roll numbers must be positive whole numbers.")
            if student.roll_no in student_index:
                raise ValueError("The student data file contains duplicate roll numbers.")
            student_index[student.roll_no] = student

        if not isinstance(saved_next_roll_no, int) or saved_next_roll_no < 1:
            saved_next_roll_no = 1
        self.students = students
        self._students_by_roll = student_index
        largest_roll_no = max(student_index, default=0) + 1
        self.next_roll_no = max(largest_roll_no, saved_next_roll_no)


class StudentManagementApp:
    def __init__(self, root, classroom):
        self.root = root
        self.classroom = classroom
        self.root.title("Student Management System")
        self.root.geometry("1180x760")
        self.root.minsize(980, 650)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self._configure_style()
        self._build_interface()
        self.refresh_students()

    def _configure_style(self):
        self.colors = {
            "background": "#F3F5FA",
            "surface": "#FFFFFF",
            "sidebar": "#172033",
            "sidebar_muted": "#A7B0C0",
            "text": "#172033",
            "muted": "#778198",
            "border": "#E5E9F1",
            "accent": "#5B5CE2",
            "accent_hover": "#494ACB",
            "soft_accent": "#EEEFFF",
            "danger": "#C2414B",
        }
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(
            "TFrame",
            background=self.colors["background"],
        )
        style.configure(
            "TLabel",
            background=self.colors["surface"],
            foreground=self.colors["text"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "PageTitle.TLabel",
            background=self.colors["background"],
            foreground=self.colors["text"],
            font=("Segoe UI", 23, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.colors["background"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "PanelTitle.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["text"],
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "PanelHint.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "FormLabel.TLabel",
            background=self.colors["surface"],
            foreground="#4B5568",
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "TEntry",
            padding=(8, 5),
            fieldbackground="#FFFFFF",
            foreground=self.colors["text"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
            insertcolor=self.colors["text"],
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", self.colors["accent"])],
            lightcolor=[("focus", self.colors["accent"])],
            darkcolor=[("focus", self.colors["accent"])],
        )
        style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground="#FFFFFF",
            padding=(12, 9),
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[
                ("pressed", self.colors["accent_hover"]),
                ("active", self.colors["accent_hover"]),
            ],
            foreground=[("disabled", "#D7D8F7")],
        )
        style.configure(
            "Secondary.TButton",
            background="#F5F6FA",
            foreground=self.colors["text"],
            padding=(10, 8),
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#E9EBF3"), ("pressed", "#DDE1EC")],
        )
        style.configure(
            "Danger.TButton",
            background="#FFF1F1",
            foreground=self.colors["danger"],
            padding=(10, 8),
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#FFE5E5"), ("pressed", "#FBD5D5")],
        )
        style.configure(
            "ClassroomCard.TButton",
            background="#FFFFFF",
            foreground=self.colors["text"],
            padding=(18, 18),
            anchor="w",
            justify="left",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "ClassroomCard.TButton",
            background=[("active", "#F5F6FF"), ("pressed", "#EEEFFF")],
        )
        style.configure(
            "Student.Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground=self.colors["text"],
            rowheight=36,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.map(
            "Student.Treeview",
            background=[("selected", self.colors["soft_accent"])],
            foreground=[("selected", self.colors["text"])],
        )
        style.configure(
            "Student.Treeview.Heading",
            background="#F7F8FC",
            foreground=self.colors["muted"],
            font=("Segoe UI", 8, "bold"),
            padding=(10, 11),
            relief="flat",
        )
        style.map(
            "Student.Treeview.Heading",
            background=[("active", "#EFF1F8")],
        )

    def _build_interface(self):
        self.root.configure(background=self.colors["background"])
        sidebar = tk.Frame(self.root, bg=self.colors["sidebar"], width=205)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=self.colors["sidebar"])
        brand.pack(fill="x", padx=20, pady=(25, 38))
        tk.Label(
            brand,
            text="S",
            bg=self.colors["accent"],
            fg="#FFFFFF",
            font=("Segoe UI", 15, "bold"),
            width=2,
            height=1,
            pady=5,
        ).pack(side="left")
        brand_text = tk.Frame(brand, bg=self.colors["sidebar"])
        brand_text.pack(side="left", padx=10)
        tk.Label(
            brand_text,
            text="CAMPUS",
            bg=self.colors["sidebar"],
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand_text,
            text="STUDENT PORTAL",
            bg=self.colors["sidebar"],
            fg=self.colors["sidebar_muted"],
            font=("Segoe UI", 7, "bold"),
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            sidebar,
            text="WORKSPACE",
            bg=self.colors["sidebar"],
            fg="#7D889B",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=22, pady=(0, 10))
        self.sidebar_items = {}
        self._sidebar_item(
            sidebar, "▦", "Overview", "overview", self.show_overview, active=True
        )
        self._sidebar_item(
            sidebar, "▤", "Classrooms", "classrooms", self.show_classrooms
        )

        sidebar_footer = tk.Frame(sidebar, bg=self.colors["sidebar"])
        sidebar_footer.pack(side="bottom", fill="x", padx=20, pady=22)
        tk.Frame(sidebar_footer, bg="#344056", height=1).pack(fill="x", pady=(0, 14))
        tk.Label(
            sidebar_footer,
            text="STUDENT RECORDS",
            bg=self.colors["sidebar"],
            fg="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            sidebar_footer,
            text="A simple place to keep\nyour class organized.",
            bg=self.colors["sidebar"],
            fg=self.colors["sidebar_muted"],
            justify="left",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(5, 0))

        content = tk.Frame(self.root, bg=self.colors["background"])
        content.pack(side="left", fill="both", expand=True)
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)
        self.overview_page = tk.Frame(content, bg=self.colors["background"])
        self.overview_page.grid(row=0, column=0, sticky="nsew")
        self.overview_page.rowconfigure(2, weight=1)
        self.overview_page.columnconfigure(0, weight=1)

        header = tk.Frame(self.overview_page, bg=self.colors["background"])
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(25, 18))
        self.page_title = tk.Label(
            header,
            text="Overview",
            bg=self.colors["background"],
            fg=self.colors["text"],
            font=("Segoe UI", 23, "bold"),
        )
        self.page_title.pack(anchor="w")
        self.page_subtitle = tk.Label(
            header,
            text="Manage your students and keep their details in one place.",
            bg=self.colors["background"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        self.page_subtitle.pack(anchor="w", pady=(4, 0))

        stats = tk.Frame(self.overview_page, bg=self.colors["background"])
        stats.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 18))
        for column in range(3):
            stats.columnconfigure(column, weight=1, uniform="stats")
        student_card = self._stat_card(
            stats,
            0,
            "TOTAL STUDENTS",
            "0",
            "Currently enrolled",
            accent=True,
        )
        self.count_label = student_card
        self.next_roll_label = self._stat_card(
            stats, 1, "NEXT ROLL NUMBER", "1", "Assigned automatically"
        )
        self._stat_card(stats, 2, "DIRECTORY", "Ready", "Your records are saved")

        workspace = tk.Frame(self.overview_page, bg=self.colors["background"])
        workspace.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 24))
        workspace.columnconfigure(1, weight=1)
        workspace.rowconfigure(0, weight=1)

        form = tk.Frame(
            workspace,
            bg=self.colors["surface"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            padx=13,
            pady=10,
        )
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
        self.form_title = ttk.Label(
            form, text="Add a student", style="PanelTitle.TLabel"
        )
        self.form_title.grid(row=0, column=0, columnspan=4, sticky="w")
        self.form_hint = ttk.Label(
            form,
            text="Enter the details below to create a new record.",
            style="PanelHint.TLabel",
            wraplength=265,
        )
        self.form_hint.grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 10))

        self.entries = {}
        ttk.Label(form, text="Class", style="FormLabel.TLabel").grid(
            row=2, column=0, sticky="w", pady=2, padx=(0, 8)
        )
        self.entries["class_name"] = ttk.Combobox(
            form,
            values=CLASS_OPTIONS,
            state="readonly",
            width=7,
        )
        self.entries["class_name"].grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="Section", style="FormLabel.TLabel").grid(
            row=2, column=2, sticky="w", pady=2, padx=(8, 8)
        )
        self.entries["section"] = ttk.Combobox(
            form,
            values=SECTION_OPTIONS,
            state="readonly",
            width=7,
        )
        self.entries["section"].grid(row=2, column=3, sticky="ew", pady=2)

        fields = (
            ("Name", "name"),
            ("Age", "age"),
            ("Address", "address"),
            ("Parent / guardian", "parent_name"),
            ("Parent phone", "parent_phone"),
            ("Previous result", "previous_result"),
            ("Test marks", "test_marks"),
        )
        for row, (label, key) in enumerate(fields, start=3):
            ttk.Label(form, text=label, style="FormLabel.TLabel").grid(
                row=row, column=0, sticky="w", pady=2, padx=(0, 8)
            )
            entry = ttk.Entry(form, width=19)
            entry.grid(row=row, column=1, columnspan=3, sticky="ew", pady=2)
            self.entries[key] = entry

        self.editing_roll_no = None
        self.submit_button = ttk.Button(
            form, text="Add student", command=self.add_student
        )
        self.submit_button.grid(
            row=len(fields) + 3,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(8, 4),
        )
        ttk.Button(
            form,
            text="Clear form",
            command=self.clear_form,
            style="Secondary.TButton",
        ).grid(
            row=len(fields) + 4, column=0, columnspan=4, sticky="ew"
        )

        roster = tk.Frame(
            workspace,
            bg=self.colors["surface"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            padx=17,
            pady=16,
        )
        roster.grid(row=0, column=1, sticky="nsew")
        roster.columnconfigure(0, weight=1)
        roster.rowconfigure(2, weight=1)

        roster_header = tk.Frame(roster, bg=self.colors["surface"])
        roster_header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(roster_header, text="Student directory", style="PanelTitle.TLabel").pack(
            anchor="w"
        )
        self.roster_hint = ttk.Label(
            roster_header,
            text="Browse, search, and manage student records.",
            style="PanelHint.TLabel",
        )
        self.roster_hint.pack(anchor="w", pady=(4, 0))

        search_row = ttk.Frame(roster)
        search_row.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(search_row, text="⌕", font=("Segoe UI", 16, "bold")).pack(
            side="left", padx=(0, 8)
        )
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_students())
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(
            side="left", fill="x", expand=True
        )

        columns = (
            "roll_no",
            "name",
            "class_name",
            "section",
            "age",
            "parent_phone",
        )
        self.tree = ttk.Treeview(
            roster,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Student.Treeview",
        )
        headings = {
            "roll_no": ("ROLL NO.", 80),
            "name": ("STUDENT", 145),
            "class_name": ("CLASS", 70),
            "section": ("SECTION", 70),
            "age": ("AGE", 55),
            "parent_phone": ("PARENT PHONE", 120),
        }
        for column, (heading, width) in headings.items():
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, anchor="w")
        self.tree.grid(row=2, column=0, sticky="nsew")
        self.tree.tag_configure("even", background="#FFFFFF")
        self.tree.tag_configure("odd", background="#FAFBFD")
        scrollbar = ttk.Scrollbar(roster, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<Double-1>", lambda _event: self.show_selected_details())

        actions = ttk.Frame(roster)
        actions.grid(row=3, column=0, sticky="ew", pady=(13, 0))
        ttk.Button(
            actions,
            text="Edit selected",
            command=self.edit_selected,
            style="Secondary.TButton",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            actions,
            text="View details",
            command=self.show_selected_details,
            style="Secondary.TButton",
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Remove selected",
            command=self.remove_selected,
            style="Danger.TButton",
        ).pack(side="right")

        self.selected_classroom = None
        self.classrooms_page = tk.Frame(content, bg=self.colors["background"])
        self.classrooms_page.grid(row=0, column=0, sticky="nsew")
        self.classrooms_page.rowconfigure(2, weight=1)
        self.classrooms_page.columnconfigure(0, weight=1)

        classrooms_header = tk.Frame(
            self.classrooms_page, bg=self.colors["background"]
        )
        classrooms_header.grid(row=0, column=0, sticky="ew", padx=28, pady=(25, 18))
        tk.Label(
            classrooms_header,
            text="Classrooms",
            bg=self.colors["background"],
            fg=self.colors["text"],
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w")
        self.classrooms_summary = tk.Label(
            classrooms_header,
            text="Browse students by class and section.",
            bg=self.colors["background"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        self.classrooms_summary.pack(anchor="w", pady=(4, 0))

        classroom_toolbar = tk.Frame(
            self.classrooms_page, bg=self.colors["background"]
        )
        classroom_toolbar.grid(
            row=1, column=0, sticky="ew", padx=28, pady=(0, 14)
        )
        classroom_toolbar.columnconfigure(1, weight=1)
        ttk.Label(classroom_toolbar, text="Find classroom").grid(
            row=0, column=0, sticky="w", padx=(0, 12)
        )
        self.classroom_search_var = tk.StringVar()
        self.classroom_search_var.trace_add(
            "write", lambda *_: self.refresh_classrooms()
        )
        classroom_search = ttk.Entry(
            classroom_toolbar, textvariable=self.classroom_search_var
        )
        classroom_search.grid(row=0, column=1, sticky="ew")
        ttk.Button(
            classroom_toolbar,
            text="Clear",
            command=lambda: self.classroom_search_var.set(""),
            style="Secondary.TButton",
        ).grid(row=0, column=2, padx=(8, 0))

        classrooms_panel = tk.Frame(
            self.classrooms_page,
            bg=self.colors["surface"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            padx=17,
            pady=16,
        )
        classrooms_panel.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 24))
        classrooms_panel.rowconfigure(0, weight=1)
        classrooms_panel.columnconfigure(0, weight=1)
        self.classrooms_canvas = tk.Canvas(
            classrooms_panel,
            background=self.colors["surface"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.classrooms_canvas.grid(row=0, column=0, sticky="nsew")
        classrooms_scrollbar = ttk.Scrollbar(
            classrooms_panel,
            orient="vertical",
            command=self.classrooms_canvas.yview,
        )
        classrooms_scrollbar.grid(row=0, column=1, sticky="ns")
        self.classrooms_canvas.configure(yscrollcommand=classrooms_scrollbar.set)
        self.classroom_cards = tk.Frame(
            self.classrooms_canvas, bg=self.colors["surface"]
        )
        self.classroom_cards_window = self.classrooms_canvas.create_window(
            (0, 0), window=self.classroom_cards, anchor="nw"
        )
        self.classroom_grid_columns = 3
        self.classroom_cards.bind(
            "<Configure>",
            lambda _event: self.classrooms_canvas.configure(
                scrollregion=self.classrooms_canvas.bbox("all")
            ),
        )
        self.classrooms_canvas.bind(
            "<Configure>",
            self._resize_classroom_grid,
        )
        for column in range(3):
            self.classroom_cards.columnconfigure(
                column, weight=1, uniform="classrooms"
            )
        self.overview_page.tkraise()

    def _sidebar_item(self, parent, icon, label, page, command, active=False):
        background = "#29334A" if active else self.colors["sidebar"]
        row = tk.Frame(parent, bg=background, height=42)
        row.pack(fill="x", padx=12, pady=3)
        row.pack_propagate(False)
        indicator = tk.Frame(
            row,
            bg=self.colors["accent"] if active else self.colors["sidebar"],
            width=3,
        )
        indicator.pack(side="left", fill="y")
        icon_label = tk.Label(
            row,
            text=icon,
            bg=background,
            fg="#BFC7D5" if not active else "#FFFFFF",
            font=("Segoe UI", 12),
            width=3,
        )
        icon_label.pack(side="left", padx=(7, 3))
        text_label = tk.Label(
            row,
            text=label,
            bg=background,
            fg="#FFFFFF" if active else self.colors["sidebar_muted"],
            font=("Segoe UI", 9, "bold" if active else "normal"),
        )
        text_label.pack(side="left")
        for widget in (row, icon_label, text_label):
            widget.bind("<Button-1>", lambda _event: command())
        self.sidebar_items[page] = (row, indicator, icon_label, text_label)

    def _set_active_sidebar_item(self, active_page):
        for page, widgets in self.sidebar_items.items():
            row, indicator, icon_label, text_label = widgets
            active = page == active_page
            background = "#29334A" if active else self.colors["sidebar"]
            row.configure(bg=background)
            indicator.configure(
                bg=self.colors["accent"] if active else self.colors["sidebar"]
            )
            icon_label.configure(
                bg=background, fg="#FFFFFF" if active else "#BFC7D5"
            )
            text_label.configure(
                bg=background,
                fg="#FFFFFF" if active else self.colors["sidebar_muted"],
                font=("Segoe UI", 9, "bold" if active else "normal"),
            )

    @staticmethod
    def _classroom_label(class_name, section):
        if not class_name and not section:
            return "Unassigned"
        label = "Class {}".format(class_name) if class_name else "Unassigned"
        return "{} - {}".format(label, section) if section else label

    def show_overview(self):
        self.selected_classroom = None
        self.page_title.configure(text="Overview")
        self.page_subtitle.configure(
            text="Manage your students and keep their details in one place."
        )
        self.overview_page.tkraise()
        self._set_active_sidebar_item("overview")
        self.refresh_students()

    def show_classrooms(self):
        self.refresh_classrooms()
        self.classrooms_page.tkraise()
        self._set_active_sidebar_item("classrooms")

    def _resize_classroom_grid(self, event):
        self.classrooms_canvas.itemconfigure(
            self.classroom_cards_window, width=event.width
        )
        columns = max(1, min(3, event.width // 250))
        if columns != self.classroom_grid_columns:
            self.classroom_grid_columns = columns
            self.refresh_classrooms()

    def open_classroom(self, class_name, section):
        self.selected_classroom = (class_name, section)
        self.clear_form()
        self.search_var.set("")
        label = self._classroom_label(class_name, section)
        self.page_title.configure(text=label)
        self.page_subtitle.configure(text="Students assigned to this classroom.")
        self.overview_page.tkraise()
        self._set_active_sidebar_item("classrooms")
        self.refresh_students()

    def refresh_classrooms(self):
        for child in self.classroom_cards.winfo_children():
            child.destroy()

        classroom_counts = self.classroom.get_classroom_counts()
        student_count = len(self.classroom.students)
        classroom_count = len(classroom_counts)
        self.classrooms_summary.configure(
            text="{} classroom{} · {} student{}".format(
                classroom_count,
                "" if classroom_count == 1 else "s",
                student_count,
                "" if student_count == 1 else "s",
            )
        )
        query = self.classroom_search_var.get().strip().casefold()
        matching_classrooms = []
        for (class_name, section), count in classroom_counts.items():
            label = self._classroom_label(class_name, section)
            if not query or query in label.casefold():
                matching_classrooms.append(
                    ((class_name, section), count, label)
                )

        columns = self.classroom_grid_columns
        for column in range(3):
            self.classroom_cards.columnconfigure(
                column, weight=1 if column < columns else 0
            )

        if not matching_classrooms:
            if classroom_count:
                message = "No classrooms match your search. Clear the search to see them all."
            else:
                message = "No classrooms yet. Add a student and assign a class and section."
            ttk.Label(
                self.classroom_cards,
                text=message,
                style="PanelHint.TLabel",
                wraplength=460,
            ).grid(row=0, column=0, columnspan=columns, sticky="w", padx=8, pady=8)
            return

        for index, ((class_name, section), count, label) in enumerate(
            matching_classrooms
        ):
            button = ttk.Button(
                self.classroom_cards,
                text="{}\n{} student{}".format(
                    label, count, "" if count == 1 else "s"
                ),
                command=lambda class_name=class_name, section=section: self.open_classroom(
                    class_name, section
                ),
                style="ClassroomCard.TButton",
            )
            button.grid(
                row=index // columns,
                column=index % columns,
                sticky="ew",
                padx=8,
                pady=8,
            )

    def _stat_card(self, parent, column, title, value, note, accent=False):
        background = self.colors["accent"] if accent else self.colors["surface"]
        foreground = "#FFFFFF" if accent else self.colors["text"]
        secondary = "#E0E1FF" if accent else self.colors["muted"]
        card = tk.Frame(
            parent,
            bg=background,
            highlightthickness=0 if accent else 1,
            highlightbackground=self.colors["border"],
            padx=16,
            pady=12,
        )
        card.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=(0, 12) if column < 2 else (0, 0),
        )
        tk.Label(
            card,
            text=title,
            bg=background,
            fg=secondary,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        value_label = tk.Label(
            card,
            text=value,
            bg=background,
            fg=foreground,
            font=("Segoe UI", 20, "bold"),
        )
        value_label.pack(anchor="w", pady=(3, 0))
        tk.Label(
            card,
            text=note,
            bg=background,
            fg=secondary,
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(1, 0))
        return value_label

    def add_student(self):
        student = self._student_from_form(self.classroom.next_roll_no)
        if student is None:
            return

        try:
            self.classroom.add_student(student)
        except (OSError, csv.Error) as error:
            messagebox.showerror("Could not save student", str(error), parent=self.root)
            return

        self.clear_form()
        self.refresh_students()
        self.refresh_classrooms()
        messagebox.showinfo(
            "Student added",
            "Student added with roll number {}.".format(student.roll_no),
            parent=self.root,
        )

    def _student_from_form(self, roll_no):
        values = {key: entry.get().strip() for key, entry in self.entries.items()}
        missing = [key.replace("_", " ") for key, value in values.items() if not value]
        if missing:
            messagebox.showerror(
                "Missing information",
                "Please fill in: " + ", ".join(missing) + ".",
                parent=self.root,
            )
            return None

        try:
            age = int(values["age"])
            if age < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid age", "Age must be a positive whole number.", parent=self.root)
            return None

        phone = values["parent_phone"]
        if len(phone) != 10 or not phone.isdigit():
            messagebox.showerror(
                "Invalid phone number",
                "Parent phone must contain exactly 10 digits.",
                parent=self.root,
            )
            return None

        values["section"] = values["section"].upper()
        return Student(
            roll_no,
            values["name"],
            age,
            values["address"],
            values["parent_name"],
            phone,
            values["previous_result"],
            values["test_marks"],
            values["class_name"],
            values["section"],
        )

    def edit_selected(self):
        student = self._selected_student()
        if student is None:
            return

        self._load_student_into_form(student)

    def _load_student_into_form(self, student):
        self.editing_roll_no = student.roll_no
        for key in self.entries:
            entry = self.entries[key]
            value = str(getattr(student, key, ""))
            if key in ("class_name", "section"):
                entry.set(value)
            else:
                entry.delete(0, tk.END)
                entry.insert(0, value)
        self.form_title.configure(text="Edit student record")
        self.form_hint.configure(
            text="Update the details below. The roll number will stay the same."
        )
        self.submit_button.configure(text="Save changes", command=self.update_student)
        self.entries["name"].focus_set()

    def update_student(self):
        if self.editing_roll_no is None:
            return
        student = self._student_from_form(self.editing_roll_no)
        if student is None:
            return

        try:
            self.classroom.update_student(student)
        except (OSError, csv.Error) as error:
            messagebox.showerror("Could not save changes", str(error), parent=self.root)
            return

        self.clear_form()
        self.refresh_students()
        self.refresh_classrooms()
        messagebox.showinfo(
            "Student updated",
            "Changes to {} (roll number {}) have been saved.".format(
                student.name, student.roll_no
            ),
            parent=self.root,
        )

    def clear_form(self):
        for key, entry in self.entries.items():
            if key in ("class_name", "section"):
                entry.set("")
            else:
                entry.delete(0, tk.END)
        self.editing_roll_no = None
        self.form_title.configure(text="Add a student")
        self.form_hint.configure(text="Enter the details below to create a new record.")
        self.submit_button.configure(text="Add student", command=self.add_student)
        if self.selected_classroom is not None:
            class_name, section = self.selected_classroom
            self.entries["class_name"].set(class_name)
            self.entries["section"].set(section)
        self.entries["name"].focus_set()

    def refresh_students(self):
        query = self.search_var.get().strip().casefold() if hasattr(self, "search_var") else ""
        for item in self.tree.get_children():
            self.tree.delete(item)
        row_number = 0
        students = self.classroom.students
        if self.selected_classroom is not None:
            students = self.classroom.get_students_for_classroom(
                *self.selected_classroom
            )
        for student in students:
            class_name = getattr(student, "class_name", "") or ""
            section = getattr(student, "section", "") or ""
            if query and query not in str(student.roll_no).casefold() and query not in student.name.casefold():
                continue
            self.tree.insert(
                "",
                "end",
                iid=str(student.roll_no),
                values=(
                    student.roll_no,
                    student.name,
                    class_name or "—",
                    section or "—",
                    student.age,
                    student.parent_phone,
                ),
                tags=("even" if row_number % 2 == 0 else "odd",),
            )
            row_number += 1
        self.count_label.configure(text=str(len(self.classroom.students)))
        self.next_roll_label.configure(text=str(self.classroom.next_roll_no))
        if self.selected_classroom is None:
            self.roster_hint.configure(
                text="Browse, search, and manage student records. {} total.".format(
                    len(self.classroom.students)
                )
            )
        else:
            self.roster_hint.configure(
                text="{} student{} in this classroom.".format(
                    row_number, "" if row_number == 1 else "s"
                )
            )

    def _selected_student(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "No student selected",
                "Select a student from the roster first.",
                parent=self.root,
            )
            return None
        return self.classroom.get_student(int(selection[0]))

    def show_selected_details(self):
        student = self._selected_student()
        if student is None:
            return

        window = tk.Toplevel(self.root)
        window.title("Student details")
        window.resizable(False, False)
        window.transient(self.root)
        details = (
            ("Roll number", student.roll_no),
            ("Name", student.name),
            ("Class", getattr(student, "class_name", "") or "Unassigned"),
            ("Section", getattr(student, "section", "") or "—"),
            ("Age", student.age),
            ("Address", student.address),
            ("Parent / guardian", student.parent_name),
            ("Parent phone", student.parent_phone),
            ("Previous result", student.previous_result),
            ("Test marks", student.test_marks),
        )
        frame = ttk.Frame(window, padding=18)
        frame.pack(fill="both", expand=True)
        for row, (label, value) in enumerate(details):
            ttk.Label(frame, text=label + ":", font=("", 10, "bold")).grid(
                row=row, column=0, sticky="nw", padx=(0, 14), pady=4
            )
            ttk.Label(frame, text=str(value), wraplength=320).grid(
                row=row, column=1, sticky="nw", pady=4
            )
        actions = ttk.Frame(frame)
        actions.grid(
            row=len(details), column=0, columnspan=2, sticky="e", pady=(12, 0)
        )
        ttk.Button(
            actions,
            text="Edit details",
            command=lambda: self.edit_details_from_window(
                student.roll_no, window
            ),
            style="Accent.TButton",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            actions, text="Close", command=window.destroy, style="Secondary.TButton"
        ).pack(side="left")
        window.bind("<Escape>", lambda _event: window.destroy())
        window.grab_set()

    def edit_details_from_window(self, roll_no, window):
        student = self.classroom.get_student(roll_no)
        if student is None:
            messagebox.showerror(
                "Could not edit student",
                "This student record is no longer available.",
                parent=window,
            )
            return

        window.destroy()
        class_name = getattr(student, "class_name", "") or ""
        section = getattr(student, "section", "") or ""
        self.open_classroom(class_name, section)
        self.tree.selection_set(str(student.roll_no))
        self._load_student_into_form(student)

    def remove_selected(self):
        student = self._selected_student()
        if student is None:
            return
        if not messagebox.askyesno(
            "Remove student",
            "Remove {} (roll number {})?".format(student.name, student.roll_no),
            parent=self.root,
        ):
            return

        try:
            self.classroom.remove_student(student.roll_no)
        except (OSError, csv.Error) as error:
            messagebox.showerror("Could not save changes", str(error), parent=self.root)
            return
        self.refresh_students()
        self.refresh_classrooms()

    def close(self):
        try:
            self.classroom.save_details()
        except (OSError, csv.Error) as error:
            messagebox.showerror("Could not save data", str(error), parent=self.root)
            return
        self.root.destroy()


def main():
    classroom = Classroom()
    root = tk.Tk()
    StudentManagementApp(root, classroom)
    root.mainloop()


if __name__ == "__main__":
    main()
