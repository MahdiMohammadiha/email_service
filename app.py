from flask import Flask, render_template, url_for, request, redirect, session
from pymongo import MongoClient
from logging import getLogger, ERROR
from os import urandom

app = Flask(__name__)
app.secret_key = urandom(24)

log = getLogger("werkzeug")
log.setLevel(ERROR)

client = MongoClient("localhost", 27017)
db = client.email_service
users = db.users


@app.route("/")
def index():
    signup_status = session.pop("signup_status", None)

    username = "Guest"
    if (signup_status is not None) and (signup_status[0]):
        username = signup_status[1]

    return render_template("index.html", username=username)


@app.route("/signup/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        signup_status = [False, "Not proceed."]

        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        user = users.find_one({"username": username})

        if not (username and password):
            signup_status = [False, "Both Username, Password and Email are required."]
        elif user:
            signup_status = [False, "Username already taken."]
        else:
            try:
                users.insert_one(
                    {"username": username, "password": password, "email": email}
                )
                signup_status = [True, username]
            except Exception as error:
                signup_status = [False, type(error).__name__]

        session["signup_status"] = signup_status

        print(str(signup_status))

        if signup_status[0]:
            return redirect(url_for("index"))

    return render_template("signup.html")


@app.route("/signin/", methods=["GET", "POST"])
def signin():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        user = users.find_one({"username": username})

        if user["password"] == password:
            return redirect(url_for("index"))

    return render_template("signin.html")


@app.route("/@")
def a_a():
    return "@_@\n\tThere is nothing here, go away."
