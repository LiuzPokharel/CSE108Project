"""Checks the teacher API: own courses, roster with grades, editing a grade. Run: .venv/bin/python test_teacher.py"""
import os

os.environ["DATABASE_URL"] = "sqlite://"   # in-memory database: must be set before app.py is imported

from app import app  # noqa: E402
from models import Course, User  # noqa: E402
from seed import seed  # noqa: E402

with app.app_context():
    seed()   # same data as the slides
    ids = {c.name: c.id for c in Course.query}
    nancy = User.query.filter_by(username="nlittle").one().id
    chuck = User.query.filter_by(username="cnorris").one().id

client = app.test_client()


def login(username):
    client.get("/logout")
    client.post("/api/login", json={"username": username, "password": "password"})


def roster(name):
    return client.get(f"/api/teacher/courses/{ids[name]}/students")


def set_grade(name, student, grade):
    return client.put(f"/api/teacher/courses/{ids[name]}/students/{student}/grade", json={"grade": grade})


# Signed out, or signed in as a student: no access
assert client.get("/api/teacher/courses").status_code == 401
login("cnorris")
assert client.get("/api/teacher/courses").status_code == 403

# Dr Hepworth's slide: he teaches CS 106 and CS 162 and nothing else
login("ahepworth")
mine = {c["name"]: c for c in client.get("/api/teacher/courses").get_json()}
assert set(mine) == {"CS 106", "CS 162"}
assert mine["CS 162"]["enrolled_count"] == 4 and mine["CS 162"]["capacity"] == 4

# The CS 162 grades slide
grades = {s["name"]: s["grade"] for s in roster("CS 162").get_json()["students"]}
assert grades == {"Aditya Ranganath": 92, "Nancy Little": 78, "Yi Wen Chen": 95, "John Stuart": 76}

# Edit a grade, and it sticks
assert set_grade("CS 162", nancy, 88).status_code == 200
assert {s["name"]: s["grade"] for s in roster("CS 162").get_json()["students"]}["Nancy Little"] == 88
assert set_grade("CS 162", nancy, None).get_json()["grade"] is None   # clearing a grade is allowed

# Bad grades are refused and change nothing
for bad in (101, -1, "A+"):
    assert set_grade("CS 162", nancy, bad).status_code == 400
assert client.put(f"/api/teacher/courses/{ids['CS 162']}/students/{nancy}/grade", data="88").status_code == 400

# A student who isn't in the course
assert set_grade("CS 162", chuck, 90).status_code == 404

# Another teacher's course: can't see the roster or change grades
assert roster("Physics 121").status_code == 404
assert set_grade("Physics 121", chuck, 0).status_code == 404

print("all teacher checks passed")
