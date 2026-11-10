import os

from flask import Flask

from models import db

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrollment.db")

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_FILE
db.init_app(app)

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
