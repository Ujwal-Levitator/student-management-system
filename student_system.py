import os
import pickle
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


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
    ):
        self.roll_no = roll_no
        self.name = name
        self.age = age
        self.address = address
        self.parent_name = parent_name
        self.parent_phone = parent_phone
        self.previous_result = previous_result
        self.test_marks = test_marks


class _StudentUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "__main__" and name == "Student":
            return Student
        return super().find_class(module, name)


class Classroom:
    def __init__(self, data_file=None):
        self.data_file = Path(data_file) if data_file else Path(__file__).with_name(
            "student_details.dat"
        )
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
        data = {
            "students": self.students,
            "next_roll_no": self.next_roll_no,
        }
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=str(self.data_file.parent),
                prefix=self.data_file.name + ".",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(str(temporary_path), str(self.data_file))
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def load_details(self):
        try:
            with self.data_file.open("rb") as file:
                data = _StudentUnpickler(file).load()
        except FileNotFoundError:
            return
        except EOFError:
            return

        if not isinstance(data, dict) or not isinstance(data.get("students"), list):
            raise ValueError("The student data file has an invalid format.")

        self.students = data["students"]
        self._students_by_roll = {
            student.roll_no: student for student in self.students
        }
        largest_roll_no = max(self._students_by_roll, default=0) + 1
        saved_next_roll_no = data.get("next_roll_no", 1)
        if not isinstance(saved_next_roll_no, int) or saved_next_roll_no < 1:
            saved_next_roll_no = 1
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
            padding=(9, 8),
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
        self._sidebar_item(sidebar, "▦", "Overview", active=True)
        self._sidebar_item(sidebar, "◎", "Students")

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
        content.rowconfigure(2, weight=1)
        content.columnconfigure(0, weight=1)

        header = tk.Frame(content, bg=self.colors["background"])
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(25, 18))
        tk.Label(
            header,
            text="Overview",
            bg=self.colors["background"],
            fg=self.colors["text"],
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Manage your students and keep their details in one place.",
            bg=self.colors["background"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        stats = tk.Frame(content, bg=self.colors["background"])
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

        workspace = tk.Frame(content, bg=self.colors["background"])
        workspace.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 24))
        workspace.columnconfigure(1, weight=1)
        workspace.rowconfigure(0, weight=1)

        form = tk.Frame(
            workspace,
            bg=self.colors["surface"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            padx=17,
            pady=16,
        )
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Add a student", style="PanelTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            form,
            text="Enter the details below to create a new record.",
            style="PanelHint.TLabel",
            wraplength=265,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 14))

        self.entries = {}
        fields = (
            ("Name", "name"),
            ("Age", "age"),
            ("Address", "address"),
            ("Parent / guardian", "parent_name"),
            ("Parent phone", "parent_phone"),
            ("Previous result", "previous_result"),
            ("Test marks", "test_marks"),
        )
        for row, (label, key) in enumerate(fields, start=2):
            ttk.Label(form, text=label, style="FormLabel.TLabel").grid(
                row=row, column=0, sticky="w", pady=5, padx=(0, 8)
            )
            entry = ttk.Entry(form, width=19)
            entry.grid(row=row, column=1, sticky="ew", pady=5)
            self.entries[key] = entry

        ttk.Button(form, text="Add student", command=self.add_student).grid(
            row=len(fields) + 2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(14, 6),
        )
        ttk.Button(
            form,
            text="Clear form",
            command=self.clear_form,
            style="Secondary.TButton",
        ).grid(
            row=len(fields) + 3, column=0, columnspan=2, sticky="ew"
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
        ttk.Label(
            roster_header,
            text="Browse, search, and manage student records.",
            style="PanelHint.TLabel",
        ).pack(anchor="w", pady=(4, 0))

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

        columns = ("roll_no", "name", "age", "parent_phone")
        self.tree = ttk.Treeview(
            roster,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Student.Treeview",
        )
        headings = {
            "roll_no": ("ROLL NO.", 80),
            "name": ("STUDENT", 170),
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

    def _sidebar_item(self, parent, icon, label, active=False):
        background = "#29334A" if active else self.colors["sidebar"]
        row = tk.Frame(parent, bg=background, height=42)
        row.pack(fill="x", padx=12, pady=3)
        row.pack_propagate(False)
        if active:
            tk.Frame(row, bg=self.colors["accent"], width=3).pack(side="left", fill="y")
        tk.Label(
            row,
            text=icon,
            bg=background,
            fg="#BFC7D5" if not active else "#FFFFFF",
            font=("Segoe UI", 12),
            width=3,
        ).pack(side="left", padx=(7, 3))
        tk.Label(
            row,
            text=label,
            bg=background,
            fg="#FFFFFF" if active else self.colors["sidebar_muted"],
            font=("Segoe UI", 9, "bold" if active else "normal"),
        ).pack(side="left")

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
        values = {key: entry.get().strip() for key, entry in self.entries.items()}
        missing = [key.replace("_", " ") for key, value in values.items() if not value]
        if missing:
            messagebox.showerror(
                "Missing information",
                "Please fill in: " + ", ".join(missing) + ".",
                parent=self.root,
            )
            return

        try:
            age = int(values["age"])
            if age < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid age", "Age must be a positive whole number.", parent=self.root)
            return

        phone = values["parent_phone"]
        if len(phone) != 10 or not phone.isdigit():
            messagebox.showerror(
                "Invalid phone number",
                "Parent phone must contain exactly 10 digits.",
                parent=self.root,
            )
            return

        student = Student(
            self.classroom.next_roll_no,
            values["name"],
            age,
            values["address"],
            values["parent_name"],
            phone,
            values["previous_result"],
            values["test_marks"],
        )
        try:
            self.classroom.add_student(student)
        except (OSError, pickle.PickleError) as error:
            messagebox.showerror("Could not save student", str(error), parent=self.root)
            return

        self.clear_form()
        self.refresh_students()
        messagebox.showinfo(
            "Student added",
            "Student added with roll number {}.".format(student.roll_no),
            parent=self.root,
        )

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.entries["name"].focus_set()

    def refresh_students(self):
        query = self.search_var.get().strip().casefold() if hasattr(self, "search_var") else ""
        for item in self.tree.get_children():
            self.tree.delete(item)
        row_number = 0
        for student in self.classroom.students:
            if query and query not in str(student.roll_no).casefold() and query not in student.name.casefold():
                continue
            self.tree.insert(
                "",
                "end",
                iid=str(student.roll_no),
                values=(
                    student.roll_no,
                    student.name,
                    student.age,
                    student.parent_phone,
                ),
                tags=("even" if row_number % 2 == 0 else "odd",),
            )
            row_number += 1
        self.count_label.configure(
            text=str(len(self.classroom.students))
        )
        self.next_roll_label.configure(text=str(self.classroom.next_roll_no))

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
        details = (
            ("Roll number", student.roll_no),
            ("Name", student.name),
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
        ttk.Button(frame, text="Close", command=window.destroy).grid(
            row=len(details), column=0, columnspan=2, sticky="e", pady=(12, 0)
        )

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
        except (OSError, pickle.PickleError) as error:
            messagebox.showerror("Could not save changes", str(error), parent=self.root)
            return
        self.refresh_students()

    def close(self):
        try:
            self.classroom.save_details()
        except (OSError, pickle.PickleError) as error:
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
