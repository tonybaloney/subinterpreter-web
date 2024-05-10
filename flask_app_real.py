# Something beyond a basic "hello world" demo for flask.
from flask import Flask, render_template
from flask_app.models import db, User
from rich.progress import track
import mimesis

SEED_USERS = 1_000

app = Flask(__name__, template_folder="flask_app/templates")

@app.route("/")
def index():
    return "Hello World!"

@app.route("/users")
def user_list():
    return render_template("list.html", users=User.select())

def seed():
    for _ in track(range(SEED_USERS), "seeding temporary database"):
        user = User(
            name=mimesis.Person().full_name(),
            email=mimesis.Person().email(),
            birthday=mimesis.Person().birthdate(),
        )
        user.save()

if __name__ == "__main__":
    db.connect()
    db.create_tables([User])
    if User.select().count() == 0:
        seed()
    app.run()
