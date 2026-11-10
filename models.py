"""Database tables: users (students, teachers, admins), courses, and enrollments.

Kept separate from app.py so teammates working on routes and pages don't edit the same file.
"""
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

ROLES = ("student", "teacher", "admin")


class User(UserMixin, db.Model):
    """Anyone who can log in. One table for all three roles; `role` says which pages they get."""
    __tablename__ = "users"   # "user" is a reserved word in Postgres, so avoid it in case we switch databases

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)   # never the password itself
    name = db.Column(db.String(100), nullable=False)            # shown as "Welcome <name>!"
    role = db.Column(db.String(10), nullable=False)
    __table_args__ = (db.CheckConstraint(f"role IN {ROLES}", name="valid_role"),)

    courses_taught = db.relationship("Course", back_populates="teacher")
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __str__(self):   # how Flask-Admin shows a user in dropdowns
        return self.name


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # e.g. "CS 106"
    time = db.Column(db.String(50), nullable=False)                # e.g. "MWF 2:00-2:50 PM"
    capacity = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    __table_args__ = (db.CheckConstraint("capacity > 0", name="positive_capacity"),)

    teacher = db.relationship("User", back_populates="courses_taught")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    @property
    def enrolled_count(self):
        return len(self.enrollments)

    @property
    def is_full(self):
        return self.enrolled_count >= self.capacity

    def __str__(self):
        return self.name


class Enrollment(db.Model):
    """One student in one course. The grade lives here: it belongs to that pair, not to the student or the course."""
    __tablename__ = "enrollments"

    # Two-column primary key: the database itself refuses to enroll the same student in the same course twice.
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), primary_key=True)
    grade = db.Column(db.Float)   # empty (None) until the teacher enters one

    student = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")


@event.listens_for(Engine, "connect")
def enforce_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores foreign keys unless asked, so e.g. deleting a teacher would leave courses
    pointing at nobody. This turns the check on for every connection."""
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        dbapi_connection.execute("PRAGMA foreign_keys = ON")
