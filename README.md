# Student Management System

A desktop student management application built with Python and Tkinter. It provides a dashboard for maintaining student records in a local data file.

## Features

- Add students with roll number, name, age, address, guardian details, previous result, and test marks.
- Assign roll numbers automatically.
- Search students by roll number or name.
- View complete details for a selected student.
- Remove students from the directory.
- Save records automatically to a local binary data file.
- Use an atomic save operation to reduce the risk of corrupted data.

## Requirements

- Python 3
- Tkinter, included with standard Python installations on most platforms

## Run the Application

From the project directory, run:

```bash
python student_system.py
```

The application stores its data in `student_details.dat` beside `student_system.py`.

## Data Fields

Each student record contains:

- Roll number
- Name
- Age
- Address
- Parent or guardian name
- Parent phone number
- Previous result
- Test marks

Parent phone numbers must contain exactly 10 digits. Age must be a positive whole number.

## Project Files

- `student_system.py` - Tkinter application and student data management.
- `student_details.dat` - Local serialized student records.
- `WORKLOG.md` - Development and change history.
