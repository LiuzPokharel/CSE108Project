"""Checks login, logout, and role-based page access. Run: .venv/bin/python test_login.py"""
import os

os.environ["DATABASE_URL"] = "sqlite://"   # in-memory database: must be set before app.py is imported

from app import app  # noqa: E402
from models import User, db  # noqa: E402

with app.app_context():
    for username, name, role in [("cnorris", "Chuck", "student"), ("ahepworth", "Dr Hepworth", "teacher")]:
        user = User(username=username, name=name, role=role)
        user.set_password("secret")
        db.session.add(user)
    db.session.commit()

client = app.test_client()   # a fake browser that keeps cookies between requests


def login(username, password):
    return client.post("/api/login", json={"username": username, "password": password})


# Signed out: pages send you to the login form, the API says "log in"
assert client.get("/").status_code == 200
assert client.get("/student").headers["Location"] == "/"
assert client.get("/api/me").status_code == 401
assert client.get("/student.html").status_code == 404   # signed-in pages aren't public files

# Wrong password and unknown username get the same answer
assert login("cnorris", "wrong").get_json() == {"error": "Wrong username or password"}
assert login("nobody", "secret").get_json() == {"error": "Wrong username or password"}

# Student signs in and lands on the student page only
r = login("cnorris", "secret")
assert r.status_code == 200 and r.get_json()["home"] == "/student"
assert client.get("/api/me").get_json() == {"name": "Chuck", "role": "student"}
assert client.get("/student").status_code == 200
assert client.get("/teacher").headers["Location"] == "/student"   # wrong role: back to your own page
assert client.get("/").headers["Location"] == "/student"          # already signed in: skip the form

# Sign out really signs out
client.get("/logout")
assert client.get("/api/me").status_code == 401

# Teacher gets the teacher page, not the student one
assert login("ahepworth", "secret").get_json()["home"] == "/teacher"
assert client.get("/teacher").status_code == 200
assert client.get("/student").headers["Location"] == "/teacher"

print("all login checks passed")
