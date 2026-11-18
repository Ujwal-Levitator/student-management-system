# Work Log

Append an entry whenever the program or its data changes.

## 2026-11-15 - Student management dashboard

- Added a Tkinter GUI for adding, searching, viewing, and removing student records.
- Improved record lookup, input validation, and reliable saving while preserving the existing data format.
- Refreshed the interface with a sidebar, summary cards, and a styled student directory.
- Replaced the local data file contents with five fictional demo students using placeholder phone numbers.
- Verified GUI initialization and search, plus data loading and persistence.

## 2026-11-18 - Project documentation

- Added a README with setup instructions, feature details, data fields, and project file descriptions.

## 2026-11-18 - Edit student records

- Added an edit flow that loads a selected student's details into the form and keeps their roll number unchanged.
- Reused the existing form validation and persisted updates with rollback if saving fails.
- Documented the edit feature and added tests for update persistence and failure handling.

## 2026-11-18 - Classroom organization

- Added class and section dropdowns to student creation and editing.
- Added a Classrooms page with classroom cards that open a filtered student roster.
- Kept older student records available under an Unassigned classroom.
- Changed the section field to an A-D dropdown and tightened the form layout so the lower fields remain visible.
- Added classroom search, responsive card columns, and an edit shortcut in the student details window.

## 2026-11-18 - CSV storage

- Switched the active student data store to an atomic UTF-8 CSV file.
- Added a one-time migration from the legacy binary file while preserving it as a backup.
- Kept next roll number metadata in the CSV so deleted roll numbers are not reused after restart.
