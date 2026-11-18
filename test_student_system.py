import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from student_system import Classroom, Student


class ClassroomUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temporary_directory.name) / "students.dat"
        self.classroom = Classroom(self.data_file)
        self.original_student = Student(
            1, "Alex", 15, "North Street", "Jordan", "1234567890", "B", "85"
        )
        self.classroom.add_student(self.original_student)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_update_persists_changes_without_changing_roll_number(self):
        updated_student = Student(
            1, "Alex Rivera", 16, "South Street", "Jordan", "1234567890", "A", "92"
        )

        self.assertTrue(self.classroom.update_student(updated_student))

        reloaded_classroom = Classroom(self.data_file)
        saved_student = reloaded_classroom.get_student(1)
        self.assertEqual(saved_student.name, "Alex Rivera")
        self.assertEqual(saved_student.age, 16)
        self.assertEqual(saved_student.address, "South Street")
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
            1, "Alex Rivera", 16, "South Street", "Jordan", "1234567890", "A", "92"
        )

        with patch.object(self.classroom, "save_details", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.classroom.update_student(updated_student)

        self.assertIs(self.classroom.get_student(1), self.original_student)
        self.assertIs(self.classroom.students[0], self.original_student)


if __name__ == "__main__":
    unittest.main()
