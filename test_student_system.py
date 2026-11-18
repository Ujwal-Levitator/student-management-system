import csv
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from student_system import Classroom, Student


class ClassroomUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temporary_directory.name) / "students.csv"
        self.classroom = Classroom(self.data_file)
        self.original_student = Student(
            1, "Alex", 15, "North Street", "Jordan", "1234567890", "B", "85"
        )
        self.classroom.add_student(self.original_student)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_update_persists_changes_without_changing_roll_number(self):
        updated_student = Student(
            1,
            "Alex Rivera",
            16,
            "South Street, Apt 2\nSecond floor",
            "Jordan",
            "1234567890",
            "A",
            "92",
        )

        self.assertTrue(self.classroom.update_student(updated_student))

        reloaded_classroom = Classroom(self.data_file)
        saved_student = reloaded_classroom.get_student(1)
        self.assertEqual(saved_student.name, "Alex Rivera")
        self.assertEqual(saved_student.age, 16)
        self.assertEqual(saved_student.address, "South Street, Apt 2\nSecond floor")
        self.assertEqual(saved_student.previous_result, "A")
        self.assertEqual(saved_student.test_marks, "92")
        self.assertEqual(reloaded_classroom.next_roll_no, 2)

    def test_update_returns_false_for_unknown_roll_number(self):
        unknown_student = Student(
            9, "Casey", 15, "West Street", "Taylor", "1234567890", "B", "80"
        )

        self.assertFalse(self.classroom.update_student(unknown_student))
        self.assertIs(self.classroom.get_student(1), self.original_student)

    def test_failed_save_restores_original_student(self):
        updated_student = Student(
            1,
            "Alex Rivera",
            16,
            "South Street, Apt 2\nSecond floor",
            "Jordan",
            "1234567890",
            "A",
            "92",
        )

        with patch.object(self.classroom, "save_details", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.classroom.update_student(updated_student)

        self.assertIs(self.classroom.get_student(1), self.original_student)
        self.assertIs(self.classroom.students[0], self.original_student)

    def test_class_and_section_are_persisted_and_grouped(self):
        first_student = Student(
            1,
            "Alex",
            15,
            "North Street",
            "Jordan",
            "1234567890",
            "B",
            "85",
            "10",
            "A",
        )
        second_student = Student(
            2,
            "Casey",
            15,
            "West Street",
            "Taylor",
            "1234567890",
            "A",
            "90",
            "9",
            "B",
        )
        self.classroom.update_student(first_student)
        self.classroom.add_student(second_student)

        reloaded_classroom = Classroom(self.data_file)

        self.assertEqual(
            reloaded_classroom.get_classroom_counts(),
            {("9", "B"): 1, ("10", "A"): 1},
        )
        self.assertEqual(
            [student.roll_no for student in reloaded_classroom.get_students_for_classroom(
                "10", "A"
            )],
            [1],
        )
        self.assertEqual(reloaded_classroom.get_student(1).class_name, "10")
        self.assertEqual(reloaded_classroom.get_student(1).section, "A")

    def test_legacy_record_without_class_fields_is_grouped_as_unassigned(self):
        del self.original_student.class_name
        del self.original_student.section
        self.classroom.save_details()

        reloaded_classroom = Classroom(self.data_file)

        self.assertEqual(reloaded_classroom.get_classroom_counts(), {("", ""): 1})

    def test_legacy_binary_file_migrates_to_csv_and_is_preserved(self):
        legacy_file = self.data_file.with_suffix(".dat")
        self.data_file.unlink()
        self.original_student.class_name = "10"
        self.original_student.section = "A"
        legacy_file.write_bytes(
            pickle.dumps(
                {"students": [self.original_student], "next_roll_no": 8},
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        )

        migrated_classroom = Classroom(self.data_file)

        self.assertTrue(self.data_file.exists())
        self.assertTrue(legacy_file.exists())
        self.assertEqual(migrated_classroom.next_roll_no, 8)
        self.assertEqual(migrated_classroom.get_student(1).name, "Alex")
        self.assertEqual(migrated_classroom.get_student(1).class_name, "10")
        self.assertEqual(migrated_classroom.get_student(1).section, "A")
        with self.data_file.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(rows[0]["record_type"], "metadata")
        self.assertEqual(rows[0]["next_roll_no"], "8")
        self.assertEqual(rows[1]["record_type"], "student")

    def test_next_roll_number_is_preserved_after_removing_all_students(self):
        self.classroom.remove_student(1)

        reloaded_classroom = Classroom(self.data_file)

        self.assertEqual(reloaded_classroom.students, [])
        self.assertEqual(reloaded_classroom.next_roll_no, 2)


if __name__ == "__main__":
    unittest.main()
