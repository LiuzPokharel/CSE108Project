"""Checks the student API: course list, enroll, drop, capacity. Run: .venv/bin/python test_student.py"""
import os

os.environ["DATABASE_URL"] = "sqlite://"   # in-memory database: must be set before app.py is imported

from app import app  # noqa: E402
from models import Course  # noqa: E402
from seed import seed  # noqa: E402

with app.app_context():
    seed()   # same data as the slides
    ids = {c.name: c.id for c in Course.query}

client = app.test_client()


def courses():
    return {c["name"]: c for c in client.get("/api/courses").get_json()}


def enroll(name):
    return client.post(f"/api/courses/{ids[name]}/enroll")


def drop(name):
    return client.delete(f"/api/courses/{ids[name]}/enroll")


# Signed out: no access
assert client.get("/api/courses").status_code == 401

client.post("/api/login", json={"username": "mlee", "password": "password"})

# Mindy's "Add Courses" slide: in Physics 121 and CS 106; Math 101 open; CS 162 full
c = courses()
assert {n for n in c if c[n]["enrolled"]} == {"Physics 121", "CS 106"}
assert c["Math 101"] == dict(id=ids["Math 101"], name="Math 101", teacher="Ralph Jenkins",
                             time="MWF 10:00-10:50 AM", enrolled_count=4, capacity=8, enrolled=False)

# Enroll in an open course: count goes up, it shows as hers
r = enroll("Math 101")
assert r.status_code == 201 and r.get_json()["enrolled_count"] == 5
assert courses()["Math 101"]["enrolled"]

# Refused: twice in the same course, a full course, a course that doesn't exist
assert enroll("Math 101").status_code == 409
r = enroll("CS 162")
assert r.status_code == 409 and r.get_json()["error"] == "CS 162 is full"
assert courses()["CS 162"]["enrolled_count"] == 4   # still 4/4
assert client.post("/api/courses/999/enroll").status_code == 404

# Drop: count goes down; dropping again is refused
r = drop("Math 101")
assert r.status_code == 200 and r.get_json()["enrolled_count"] == 4
assert not courses()["Math 101"]["enrolled"]
assert drop("Math 101").status_code == 404

# A dropped seat in a full course opens it up for someone else
client.get("/logout")
client.post("/api/login", json={"username": "ychen", "password": "password"})
assert drop("CS 162").status_code == 200
client.get("/logout")
client.post("/api/login", json={"username": "mlee", "password": "password"})
assert enroll("CS 162").status_code == 201

# Teachers can't use the student API
client.get("/logout")
client.post("/api/login", json={"username": "ahepworth", "password": "password"})
assert client.get("/api/courses").status_code == 403
assert enroll("Math 101").status_code == 403

print("all student checks passed")
