"""Reset the database and fill it with the people and courses from the Lab 8 slides.

Run: .venv/bin/python seed.py
WARNING: deletes everything in enrollment.db first. Every account's password is "password".
"""
from app import app
from models import Course, Enrollment, User, db

PASSWORD = "password"   # demo only: every seeded account uses it

ADMINS = [("admin", "Admin")]
TEACHERS = [("swalker", "Susan Walker"), ("ahepworth", "Ammon Hepworth"), ("rjenkins", "Ralph Jenkins")]
STUDENTS = [
    ("cnorris", "Chuck Norris"),        # student login slide
    ("mlee", "Mindy Lee"),              # "Welcome Mindy!" slide (last name made up)
    ("aranganath", "Aditya Ranganath"),  # the four on the CS 162 grades slide
    ("nlittle", "Nancy Little"),
    ("ychen", "Yi Wen Chen"),
    ("jstuart", "John Stuart"),
]

# name, teacher, time, capacity, {student: grade}. CS 162 grades are from the slides; the others are made up.
COURSES = [
    ("Physics 121", "swalker", "TR 11:00-11:50 AM", 10,
     {"cnorris": 88, "mlee": 91, "aranganath": 84, "nlittle": 73, "ychen": 97}),
    ("CS 106", "ahepworth", "MWF 2:00-2:50 PM", 10,
     {"cnorris": 79, "mlee": 85, "jstuart": 90, "aranganath": 82}),
    ("Math 101", "rjenkins", "MWF 10:00-10:50 AM", 8,
     {"nlittle": 81, "ychen": 94, "jstuart": 68, "aranganath": 87}),
    ("CS 162", "ahepworth", "TR 3:00-3:50 PM", 4,
     {"aranganath": 92, "nlittle": 78, "ychen": 95, "jstuart": 76}),
]

# What the slides show in the "Students Enrolled" column
SLIDE_COUNTS = {"Physics 121": "5/10", "CS 106": "4/10", "Math 101": "4/8", "CS 162": "4/4"}


def seed():
    db.drop_all()
    db.create_all()

    users = {}
    for role, people in (("admin", ADMINS), ("teacher", TEACHERS), ("student", STUDENTS)):
        for username, name in people:
            user = User(username=username, name=name, role=role)
            user.set_password(PASSWORD)
            users[username] = user
    db.session.add_all(users.values())

    for name, teacher, time, capacity, grades in COURSES:
        course = Course(name=name, teacher=users[teacher], time=time, capacity=capacity)
        db.session.add(course)
        for student, grade in grades.items():
            db.session.add(Enrollment(student=users[student], course=course, grade=grade))
    db.session.commit()

    # The data should reproduce the mockups exactly
    counts = {c.name: f"{c.enrolled_count}/{c.capacity}" for c in Course.query}
    assert counts == SLIDE_COUNTS, counts
    chuck = User.query.filter_by(username="cnorris").one()
    assert sorted(e.course.name for e in chuck.enrollments) == ["CS 106", "Physics 121"]


if __name__ == "__main__":
    with app.app_context():
        seed()
        print(f"Seeded {User.query.count()} users, {Course.query.count()} courses, "
              f"{Enrollment.query.count()} enrollments. Every password is \"{PASSWORD}\".")
        for role in ("admin", "teacher", "student"):
            print(f"  {role + 's':<9} " + ", ".join(u.username for u in User.query.filter_by(role=role)))
