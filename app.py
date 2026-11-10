import os
from functools import wraps

from flask import Flask, jsonify, redirect, request, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from models import User, db

HERE = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(HERE, "enrollment.db")
# static/ is public (login page, CSS, JS). pages/ is only served through routes that check the role.
PAGES = os.path.join(HERE, "pages")

app = Flask(__name__, static_folder="static", static_url_path="")
# DATABASE_URL lets the tests (or a Postgres server later) swap databases without editing this file
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///" + DB_FILE)
# Signs the login cookie so nobody can forge one. Set a real random SECRET_KEY if this ever goes online.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
db.init_app(app)

with app.app_context():
    db.create_all()

# Where each role lands after logging in
HOME = {"student": "/student", "teacher": "/teacher", "admin": "/admin"}


# --- Login machinery -------------------------------------------------------
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login keeps only the user's id in the cookie. This turns it back into a User on every request."""
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    """Not logged in: API calls get an error the JavaScript can read, pages go back to the login screen."""
    if request.path.startswith("/api/"):
        return jsonify(error="Please log in"), 401
    return redirect("/")


def role_required(role):
    """Put @role_required("student") (or "teacher") on a route so only that role gets through."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role != role:
                if request.path.startswith("/api/"):
                    return jsonify(error="Not allowed for your role"), 403
                return redirect(HOME[current_user.role])   # wrong page: send them to their own
            return view(*args, **kwargs)
        return wrapper
    return decorator


# --- Pages -------------------------------------------------------------------
@app.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(HOME[current_user.role])   # already signed in: skip the login form
    return app.send_static_file("login.html")


@app.get("/student")
@role_required("student")
def student_page():
    return send_from_directory(PAGES, "student.html")


@app.get("/teacher")
@role_required("teacher")
def teacher_page():
    return send_from_directory(PAGES, "teacher.html")


@app.get("/logout")
def logout():
    logout_user()
    return redirect("/")


# --- API -----------------------------------------------------------------------
@app.post("/api/login")
def login():
    body = request.get_json(silent=True) or {}
    user = User.query.filter_by(username=str(body.get("username", "")).strip()).first()
    # Same message whether the username or the password is wrong, so nobody can probe which usernames exist
    if user is None or not user.check_password(str(body.get("password", ""))):
        return jsonify(error="Wrong username or password"), 401
    login_user(user)
    return jsonify(name=user.name, role=user.role, home=HOME[user.role])


@app.get("/api/me")
@login_required
def me():
    """Who is signed in. Every page calls this to fill in "Welcome <name>!"."""
    return jsonify(name=current_user.name, role=current_user.role)


if __name__ == "__main__":
    app.run(debug=True)
