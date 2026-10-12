"""Functional + edge-case tests. Run: python -m unittest test_api -v"""
import os
import tempfile
import unittest

import app as student_app

VALID = {"roll_no": "CS101", "name": "Asha Verma", "class": "10-A",
         "marks": 87.5, "contact": "9876543210", "email": "asha@example.com"}


class StudentAPITests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        student_app.app.config["DATABASE"] = self.path
        student_app.init_db()
        self.c = student_app.app.test_client()

    def tearDown(self):
        os.remove(self.path)

    def add(self, **over):
        return self.c.post("/api/students", json={**VALID, **over})

    def test_add_and_list(self):
        r = self.add()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["class"], "10-A")
        self.assertEqual(len(self.c.get("/api/students").get_json()), 1)

    def test_duplicate_roll_number(self):
        self.add()
        self.assertEqual(self.add(name="Someone Else").status_code, 409)

    def test_invalid_contact(self):
        for i, bad in enumerate(["12345", "abcdefghij", "0123456789", ""]):
            r = self.add(roll_no=f"R{i}", contact=bad)
            self.assertEqual(r.status_code, 400, bad)
            self.assertIn("contact", r.get_json()["details"])

    def test_invalid_marks_and_missing_fields(self):
        self.assertEqual(self.add(marks=101).status_code, 400)
        self.assertEqual(self.add(marks="abc").status_code, 400)
        self.assertEqual(self.c.post("/api/students", json={}).status_code, 400)
        self.assertEqual(self.c.post("/api/students", data="nope").status_code, 400)

    def test_search_by_name_and_roll(self):
        self.add()
        self.add(roll_no="CS102", name="Rohan Das", contact="9123456780")
        self.assertEqual(len(self.c.get("/api/students?q=asha").get_json()), 1)
        self.assertEqual(len(self.c.get("/api/students?q=CS10").get_json()), 2)

    def test_search_nonexistent(self):
        self.add()
        r = self.c.get("/api/students?q=zzzz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), [])

    def test_update(self):
        sid = self.add().get_json()["id"]
        r = self.c.put(f"/api/students/{sid}", json={**VALID, "marks": 91})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["marks"], 91)

    def test_update_to_duplicate_roll(self):
        self.add()
        sid = self.add(roll_no="CS102", contact="9123456780").get_json()["id"]
        self.assertEqual(self.c.put(f"/api/students/{sid}", json=VALID).status_code, 409)

    def test_nonexistent_student(self):
        self.assertEqual(self.c.put("/api/students/999", json=VALID).status_code, 404)
        self.assertEqual(self.c.delete("/api/students/999").status_code, 404)
        self.assertEqual(self.c.get("/api/students/999").status_code, 404)

    def test_delete(self):
        sid = self.add().get_json()["id"]
        self.assertEqual(self.c.delete(f"/api/students/{sid}").status_code, 200)
        self.assertEqual(self.c.get("/api/students").get_json(), [])


if __name__ == "__main__":
    unittest.main()
