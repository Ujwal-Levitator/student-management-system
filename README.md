# Student Management System

A desktop student management application built with Python and Tkinter. It provides a dashboard for maintaining student records in a local data file.

## Features

- Add students with roll number, name, age, address, guardian details, previous result, and test marks.
- Assign each student to a class (1-12) and section (A-D).
- Assign roll numbers automatically.
- Search students by roll number or name.
- Search responsive classroom cards and view a filtered roster for each class and section.
- View complete details for a selected student.
- Open the edit form directly from a student's details.
- Edit student details while preserving the student's roll number.
- Remove students from the directory.
- Save records automatically to a local CSV file.
- Use an atomic save operation to reduce the risk of corrupted data.
- Migrate existing `student_details.dat` records to CSV on first launch, keeping the binary file as a backup.

## Requirements

- Python 3
- Tkinter, included with standard Python installations on most platforms

## Run the Application

From the project directory, run:

```bash
python student_system.py
```

The application stores its data in `student_details.csv` beside `student_system.py`.
If that file is missing and `student_details.dat` exists, the app migrates the
records automatically. A metadata row preserves the next roll number, and the
original binary file is retained as a backup.

## Data Fields

Each student record contains:

- Roll number
- Name
- Class (1-12) and section
- Age
- Address
- Parent or guardian name
- Parent phone number
- Previous result
- Test marks

Parent phone numbers must contain exactly 10 digits. Age must be a positive whole number.
Sections are selected from A-D and stored in uppercase. Existing records without
class or section information appear under **Unassigned** in the classroom list
until edited.

## Project Files

- `student_system.py` - Tkinter application and student data management.
- `student_details.csv` - Local student records in CSV format.
- `student_details.dat` - Legacy binary data retained as a migration backup.
- `WORKLOG.md` - Development and change history.
