from tag_maker import p_lightred
from flask import Flask, render_template, url_for, request, redirect, session
from pymongo import MongoClient
from logging import getLogger, ERROR
from os import urandom

# TODO: make a "response" variable and remove other "return"s in each function; signin to index message

app = Flask(__name__)
app.secret_key = urandom(24)

log = getLogger("werkzeug")
# log.setLevel(ERROR)

client = MongoClient("localhost", 27017)
db = client.email_service
users = db.users
emails = db.emails


@app.route("/")
def index():
    page_name = "Index"

    username = request.cookies.get("username")
    if not username:
        username = "Guest"

    js = False
    message = page_name
    header_bg = ""

    signin_to_index = session.pop("signin_to_index", False)
    if signin_to_index:
        js = True
        header_bg = "success-bg"
        message = "Signin successful"

    signout_to_index = session.pop("signout_to_index", False)
    if signout_to_index:
        js = True
        header_bg = "success-bg"
        message = "Signout successful"

    return render_template(
        "index.html",
        js=js,
        message=message,
        header_bg=header_bg,
        page_name=page_name,
        username=username,
    )


@app.route("/signup/", methods=["GET", "POST"])
def signup():
    page_name = "Signup"

    if request.cookies.get("username"):
        return redirect(url_for("index"))

    signup_flag = True
    message = page_name

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        signup_flag = False
        if not (username and password):
            message = "Username, Password and Email are required"
        elif users.find_one({"username": username}):
            message = "Username already taken"
        elif users.find_one({"email": email}):
            message = "Email already in use"
        else:
            try:
                users.insert_one(
                    {"username": username, "password": password, "email": email}
                )
                signup_flag = True
                message = username
            except Exception as error:
                message = type(error).__name__

        if signup_flag:
            session["signup_to_signin"] = True
            return redirect(url_for("signin"))

    header_bg = ""
    if not signup_flag:
        header_bg = "error-bg"

    js = not signup_flag

    return render_template(
        "signup.html",
        js=js,
        message=message,
        header_bg=header_bg,
        page_name=page_name,
    )


@app.route("/signin/", methods=["GET", "POST"])
def signin():
    page_name = "Signin"

    if request.cookies.get("username"):
        return redirect(url_for("index"))

    js = False
    header_bg = ""
    message = page_name

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users.find_one({"username": username})

        if user and (user["password"] == password):
            session["signin_to_index"] = True
            response = redirect(url_for("index"))
            response.set_cookie("username", username, max_age=7200)
            return response

        message = "Invalid credentials"
        header_bg = "error-bg"

    signup_to_signin = session.pop("signup_to_signin", False)
    if signup_to_signin:
        js = True
        header_bg = "success-bg"
        message = "Your account created successfully"

    signout_to_signin = session.pop("signout_to_signin", False)
    if signout_to_signin:
        js = True
        header_bg = "warning-bg"
        message = "You need to signin here first"

    return render_template(
        "signin.html",
        js=js,
        message=message,
        header_bg=header_bg,
        page_name=page_name,
    )


@app.route("/signout/")
def signout():
    if not request.cookies.get("username"):
        session["signout_to_signin"] = True
        return redirect(url_for("signin"))

    session["signout_to_index"] = True
    response = redirect(url_for("index"))
    response.set_cookie("username", "", expires=0)
    return response


@app.route("/inbox/")
def inbox():
    page_name = "Inbox"

    username = request.cookies.get("username")
    if not username:
        return redirect(url_for("signin"))

    js = False
    header_bg = ""
    message = page_name

    data = [
        {
            "index": 1,
            "from": "john@example.com",
            "subject": "Meeting Reminder",
            "date": "2024-04-20",
            "body": "Don't forget about our meeting tomorrow.",
        },
        {
            "index": 2,
            "from": "alice@example.com",
            "subject": "Project Update",
            "date": "2024-04-21",
            "body": "Here's the latest progress on our project.",
        },
        {
            "index": 3,
            "from": "bob@example.com",
            "subject": "Important Announcement",
            "date": "2024-04-22",
            "body": "Please read this important announcement carefully.",
        },
    ]

    return render_template(
        "inbox.html",
        js=js,
        message=message,
        header_bg=header_bg,
        page_name=page_name,
        username=username,
        data=data,
    )


@app.route("/sent/")
def sent():
    username = request.cookies.get("username")
    if not username:
        return redirect(url_for("signin"))

    js = False
    header_bg = ""
    message = page_name

    data = [
        {
            "index": 1,
            "to": "client1@example.com",
            "subject": "Meeting Confirmation",
            "date": "2024-04-20",
            "body": "Confirming our meeting scheduled for next week.",
        },
        {
            "index": 2,
            "to": "client2@example.com",
            "subject": "Project Update",
            "date": "2024-04-21",
            "body": "Here's the latest update on the project.",
        },
        {
            "index": 3,
            "to": "client3@example.com",
            "subject": "Invoice Attached",
            "date": "2024-04-22",
            "body": "Please find attached the invoice for the services rendered.",
        },
    ]

    return render_template(
        "sent.html",
        js=js,
        message=message,
        header_bg=header_bg,
        page_name=page_name,
        username=username,
        data=data,
    )


@app.route("/toastr")
def toastr():
    return render_template("toastr.html")


if __name__ == "__main__":
    app.run(debug=True)
