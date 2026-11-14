"""Admin page at /admin: create, read, update and delete every user, course and enrollment.

Flask-Admin builds the list, create, edit and delete screens from the models. This file only adds:
who may see them, which fields show, and the same rules the rest of the app follows.
"""
from flask import redirect
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_admin.menu import MenuLink
from flask_login import current_user
from wtforms import FloatField, PasswordField
from wtforms.validators import NumberRange, Optional, ValidationError

from models import ROLES, Course, Enrollment, User, db


class AdminOnly:
    """Mixed into every admin screen: anyone who isn't a signed-in admin goes back to the login page."""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect("/")


class Home(AdminOnly, AdminIndexView):
    pass


class AdminView(AdminOnly, ModelView):
    # Hidden token in every form, so another website can't submit these forms while an admin is signed in
    form_base_class = SecureForm


def only(role):
    """Dropdown choices limited to one role, e.g. only teachers can teach a course."""
    return {"query_factory": lambda: User.query.filter_by(role=role).order_by(User.name)}


class UserView(AdminView):
    column_list = ["username", "name", "role"]
    column_searchable_list = ["username", "name"]
    column_filters = ["role"]
    form_columns = ["username", "name", "role", "password"]   # never the stored hash
    form_choices = {"role": [(role, role.title()) for role in ROLES]}
    form_extra_fields = {
        "password": PasswordField("Password", description="Leave empty to keep the current password."),
    }

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)   # stored as a hash, same as everywhere else
        elif is_created:
            raise ValidationError("A new user needs a password.")


class CourseView(AdminView):
    column_list = ["name", "teacher", "time", "enrolled_count", "capacity"]
    column_labels = {"enrolled_count": "Students enrolled"}
    column_searchable_list = ["name", "time"]
    form_columns = ["name", "teacher", "time", "capacity"]
    form_args = {"teacher": only("teacher"), "capacity": {"validators": [NumberRange(min=1)]}}

    def on_model_change(self, form, model, is_created):
        if model.capacity < model.enrolled_count:
            raise ValidationError(f"{model.name} already has {model.enrolled_count} students, "
                                  "so its capacity can't be lower than that.")


class EnrollmentView(AdminView):
    column_list = ["student", "course", "grade"]
    column_sortable_list = [("student", "student.name"), ("course", "course.name"), "grade"]
    form_columns = ["student", "course", "grade"]
    # Name the field type outright: Flask-Admin 2.2 doesn't recognize SQLAlchemy 2.1's Float and silently drops it
    form_overrides = {"grade": FloatField}
    form_args = {
        "student": only("student"),
        "grade": {"validators": [Optional(), NumberRange(min=0, max=100)]},
    }

    def on_model_change(self, form, model, is_created):
        # Setting model.course already counts this enrollment, so "full" means over capacity here
        if model.course.enrolled_count > model.course.capacity:
            raise ValidationError(f"{model.course.name} is full ({model.course.capacity} students).")


def init_admin(app):
    admin = Admin(app, name="ACME University Admin", index_view=Home(url="/admin"))
    admin.add_view(UserView(User, db, name="Users"))
    admin.add_view(CourseView(Course, db, name="Courses"))
    admin.add_view(EnrollmentView(Enrollment, db, name="Enrollments"))
    admin.add_link(MenuLink(name="Sign out", url="/logout"))
