# ACME University: Student Enrollment Web App

CSE 108 Lab 8. Flask + SQLAlchemy (SQLite) + vanilla JS.

## Setup
```
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                   # creates enrollment.db with the data from the slides (resets it!)
python app.py                    # then open http://127.0.0.1:5000
```

## Demo accounts (password for all: `password`)
| Role | Usernames |
|---|---|
| Student | `cnorris` (Chuck), `mlee` (Mindy), `aranganath`, `nlittle`, `ychen`, `jstuart` |
| Teacher | `ahepworth`, `swalker`, `rjenkins` |
| Admin | `admin` |

## Tests
```
python test_models.py    # database rules (no double enrollment, capacity, roles, ...)
python test_login.py     # login, logout, role-based access
python test_student.py   # course list, enroll, drop, capacity
```

## Layout
| File | What |
|---|---|
| `models.py` | Tables: `User` (student/teacher/admin), `Course`, `Enrollment` (with grade) |
| `app.py` | Flask app: login, pages, API routes |
| `seed.py` | Sample data from the slides |
| `static/` | Public files: login page, CSS, JS |
| `pages/` | Signed-in pages, only served after a role check |

## API
| Method | Route | Who | What |
|---|---|---|---|
| POST | `/api/login` | anyone | `{username, password}` → `{name, role, home}` |
| GET | `/api/me` | signed in | `{name, role}` |
| GET | `/api/courses` | student | every course + `enrolled` (true if you're in it) |
| POST | `/api/courses/<id>/enroll` | student | add; 409 if full or already in |
| DELETE | `/api/courses/<id>/enroll` | student | drop; 404 if not in it |
| GET | `/api/teacher/courses` | teacher | courses assigned to the signed-in teacher |
| GET | `/api/teacher/courses/<id>/students` | teacher | enrolled students and grades for an owned course |
| PUT | `/api/teacher/courses/<id>/students/<student_id>/grade` | teacher | set a grade from 0–100, or `null` to clear it |

## Adding a route
Lock any route to a role with `@role_required`:
```python
@app.get("/api/my-courses")
@role_required("student")
def my_courses():
    return jsonify([...current_user.enrollments...])
```
Signed-out users get a 401 (API) or the login page; the wrong role gets a 403 (API) or their own page.

## Status
- [x] Database, login/logout, sample data
- [x] Student: your courses, all courses, add/drop (respecting capacity)
- [x] Teacher: your courses, students + grades, edit grade
- [ ] Admin: Flask-Admin at `/admin`
