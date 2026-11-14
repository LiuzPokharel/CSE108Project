"""Checks the admin page: who can open it, and that its forms follow the app's rules.
Run: .venv/bin/python test_admin.py"""
import os
import re

os.environ["DATABASE_URL"] = "sqlite://"   # in-memory database: must be set before app.py is imported

from app import app  # noqa: E402
from models import Course, Enrollment, User, db  # noqa: E402
from seed import seed  # noqa: E402

with app.app_context():
    seed()

client = app.test_client()


def login(username):
    client.get("/logout")
    client.post("/api/login", json={"username": username, "password": "password"})


def submit(form_url, data, post_url=None):
    """Open an admin form, copy its hidden CSRF token, and submit it like a browser would."""
    html = client.get(form_url).get_data(as_text=True)
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
    return client.post(post_url or form_url, data={**data, "csrf_token": token})


def ids():
    with app.app_context():
        users = {u.username: u.id for u in User.query}
        courses = {c.name: c.id for c in Course.query}
    return users, courses


def query(fn):
    with app.app_context():
        return fn()


users, courses = ids()

# --- Only admins get in ---------------------------------------------------
assert client.get("/admin/").headers["Location"] == "/"            # signed out
login("cnorris")
assert client.get("/admin/user/").headers["Location"] == "/"       # student
login("ahepworth")
assert client.get("/admin/course/").headers["Location"] == "/"     # teacher
login("admin")
assert client.get("/admin/").status_code == 200

# --- Users: passwords are hashed, and a new user needs one ---------------
submit("/admin/user/new/", {"username": "newkid", "name": "New Kid", "role": "student", "password": "hunter22"})
new_kid = query(lambda: User.query.filter_by(username="newkid").one())
assert new_kid.password_hash != "hunter22" and new_kid.check_password("hunter22")

submit("/admin/user/new/", {"username": "nopass", "name": "No Pass", "role": "student", "password": ""})
assert query(lambda: User.query.filter_by(username="nopass").first()) is None

# Editing without typing a password keeps the old one
submit(f"/admin/user/edit/?id={new_kid.id}", {"username": "newkid", "name": "Renamed Kid", "role": "student", "password": ""})
renamed = query(lambda: db.session.get(User, new_kid.id))
assert renamed.name == "Renamed Kid" and renamed.check_password("hunter22")

# --- Enrollments: capacity and grade range ---------------------------------
# CS 162 is 4/4 on the slides: the admin can't squeeze a fifth student in either
submit("/admin/enrollment/new/", {"student": new_kid.id, "course": courses["CS 162"], "grade": ""})
assert query(lambda: Course.query.filter_by(name="CS 162").one().enrolled_count) == 4

# Math 101 has room
submit("/admin/enrollment/new/", {"student": new_kid.id, "course": courses["Math 101"], "grade": "88"})
assert query(lambda: db.session.get(Enrollment, (new_kid.id, courses["Math 101"])).grade) == 88

# Grades outside 0-100 are refused; a valid edit goes through
edit = f"/admin/enrollment/edit/?id={new_kid.id},{courses['Math 101']}"
submit(edit, {"student": new_kid.id, "course": courses["Math 101"], "grade": "150"})
assert query(lambda: db.session.get(Enrollment, (new_kid.id, courses["Math 101"])).grade) == 88
submit(edit, {"student": new_kid.id, "course": courses["Math 101"], "grade": "91"})
assert query(lambda: db.session.get(Enrollment, (new_kid.id, courses["Math 101"])).grade) == 91

# --- Courses: capacity can't drop below enrollment; only teachers can teach -
cs162 = f"/admin/course/edit/?id={courses['CS 162']}"
submit(cs162, {"name": "CS 162", "teacher": users["ahepworth"], "time": "TR 3:00-3:50 PM", "capacity": "2"})
assert query(lambda: db.session.get(Course, courses["CS 162"]).capacity) == 4
submit(cs162, {"name": "CS 162", "teacher": users["cnorris"], "time": "TR 3:00-3:50 PM", "capacity": "4"})
assert query(lambda: db.session.get(Course, courses["CS 162"]).teacher.username) == "ahepworth"

# Deleting a course removes its enrollments too
submit("/admin/course/", {"id": courses["Math 101"], "url": "/admin/course/"}, post_url="/admin/course/delete/")
assert query(lambda: db.session.get(Course, courses["Math 101"])) is None
assert query(lambda: Enrollment.query.filter_by(course_id=courses["Math 101"]).count()) == 0

print("all admin checks passed")
