"""Checks the database rules. Run: .venv/bin/python test_models.py"""
import warnings

from flask import Flask
from sqlalchemy.exc import IntegrityError, SAWarning

from models import Course, Enrollment, User, db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"   # in memory: a fresh, empty database every run
db.init_app(app)
# SQLAlchemy warns when we add a duplicate on purpose; the test checks that it gets rejected anyway
warnings.filterwarnings("ignore", category=SAWarning)


def rejected(*objects):
    """True if the database refuses to save these objects."""
    db.session.add_all(objects)
    try:
        db.session.commit()
        return False
    except IntegrityError:
        db.session.rollback()
        return True


with app.app_context():
    db.create_all()

    teacher = User(username="ahepworth", name="Dr Hepworth", role="teacher")
    student = User(username="cnorris", name="Chuck", role="student")
    for u in (teacher, student):
        u.set_password("secret")
    course = Course(name="CS 162", time="TR 3:00-3:50 PM", capacity=1, teacher=teacher)
    db.session.add_all([teacher, student, course, Enrollment(student=student, course=course, grade=92)])
    db.session.commit()

    # Passwords are stored hashed and checked correctly
    assert student.password_hash != "secret" and student.check_password("secret") and not student.check_password("wrong")

    # Counts and capacity
    assert course.enrolled_count == 1 and course.is_full
    assert [e.course.name for e in student.enrollments] == ["CS 162"]
    assert [c.name for c in teacher.courses_taught] == ["CS 162"]

    # The database itself blocks bad data
    assert rejected(Enrollment(student_id=student.id, course_id=course.id))                   # enrolled twice
    assert rejected(User(username="x", name="X", role="janitor", password_hash="h"))         # unknown role
    assert rejected(User(username="cnorris", name="Copy", role="student", password_hash="h"))  # duplicate username
    assert rejected(Course(name="Bad", time="MWF", capacity=0, teacher=teacher))             # capacity 0
    assert rejected(Course(name="Ghost", time="MWF", capacity=5, teacher_id=999))            # teacher doesn't exist

    # Deleting a student removes their enrollments too, instead of leaving orphans behind
    db.session.delete(student)
    db.session.commit()
    assert Enrollment.query.count() == 0 and course.enrolled_count == 0

print("all database checks passed")
