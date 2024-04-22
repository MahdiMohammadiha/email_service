from flask import Flask, render_template, url_for, request, redirect
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


@app.route("/", methods=["GET"])
def index():
    username = request.cookies.get("username")
    if not username:
        username = "Guest"

    return render_template("index.html", username=username)


@app.route("/signup/", methods=["GET", "POST"])
def signup():
    if request.cookies.get("username"):
        return redirect(url_for("index"))

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

        if signup_status[0]:
            return redirect(url_for("signin"))

    return render_template("signup.html")


@app.route("/signin/", methods=["GET", "POST"])
def signin():
    if request.cookies.get("username"):
        return redirect(url_for("index"))

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        user = users.find_one({"username": username})

        if user and (user["password"] == password):
            response = redirect(url_for("index"))
            response.set_cookie("username", username, max_age=7200)
            return response

    return render_template("signin.html")


@app.route("/signout/")
def signout():
    if not request.cookies.get("username"):
        return redirect(url_for("index"))

    response = redirect(url_for("index"))
    response.set_cookie("username", "", expires=0)
    return response


@app.route("/@")
def a_a():
    return "@_@<br>There is nothing here, go away."


if __name__ == "__main__":
    app.run(debug=True)
