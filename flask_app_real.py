# Something beyond a basic "hello world" demo for flask.
from flask import Flask, render_template
from flask_app.models import db, User
from rich.progress import track
import mimesis
import concurrent.futures
from interpreter_cache import cache

SEED_USERS = 1_000

app = Flask(__name__, template_folder="flask_app/templates")


@app.route("/")
def index():
    return "Hello World"


def calculate_star_sign(user: User) -> tuple[User, str]:
    birthday = user.birthday
    if birthday.month == 1:
        sign = "Capricorn" if birthday.day < 20 else "Aquarius"
    elif birthday.month == 2:
        sign = "Aquarius" if birthday.day < 19 else "Pisces"
    elif birthday.month == 3:
        sign = "Pisces" if birthday.day < 21 else "Aries"
    elif birthday.month == 4:
        sign = "Aries" if birthday.day < 20 else "Taurus"
    elif birthday.month == 5:
        sign = "Taurus" if birthday.day < 21 else "Gemini"
    elif birthday.month == 6:
        sign = "Gemini" if birthday.day < 21 else "Cancer"
    elif birthday.month == 7:
        sign = "Cancer" if birthday.day < 23 else "Leo"
    elif birthday.month == 8:
        sign = "Leo" if birthday.day < 23 else "Virgo"
    elif birthday.month == 9:
        sign = "Virgo" if birthday.day < 23 else "Libra"
    elif birthday.month == 10:
        sign = "Libra" if birthday.day < 23 else "Scorpio"
    elif birthday.month == 11:
        sign = "Scorpio" if birthday.day < 22 else "Sagittarius"
    else:
        sign = "Sagittarius" if birthday.day < 22 else "Capricorn"

    return (user, sign)


@app.route("/users")
def user_list():
    if cache_value := cache.get("/users"):
        return cache_value

    users = User.select()
    enriched_users = []
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Start the load operations and mark each future with its URL
        futures = {executor.submit(calculate_star_sign, user): user for user in users}
        result = concurrent.futures.wait(futures)
        for done in result.done:
            user, sign = done.result()
            user.star_sign = sign
            enriched_users.append(user)

    result = render_template("list.html", users=enriched_users)
    cache.set("/users", result)
    return result


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
    app.run(debug=True)
