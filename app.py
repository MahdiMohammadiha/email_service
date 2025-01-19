from projectAssistant import check_auth, encrypt, decrypt
from os import urandom
from flask import Flask, render_template, url_for, request, redirect, session
from pymongo import MongoClient
from logging import getLogger, ERROR
from datetime import datetime

"""
TODO: 
    1. make a "response" variable and remove other "return"s in each function
    2. manage js variable with header_bg -- if header_bg => js = True
    3. save token in db and set a expiration time -- for dinamic token key generation
"""

app = Flask(__name__)
app.secret_key = "aa7a518cb6084aba3b85c2407e4b90e4e8c33565aaa90137e484710473e9769c"
# app.secret_key = urandom(32)

log = getLogger("werkzeug")
# log.setLevel(ERROR)

client = MongoClient("localhost", 27017)
db = client.email_service
users = db.users
emails = db.emails

PAGE_SIZE = 10


@app.route("/")
def index():
    page_name = "Index"

    username = check_auth("token", app.secret_key)
    if not username:
        username = "Gust"

    js = False
    header_bg = ""
    message = page_name

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

    if check_auth("token", app.secret_key):
        return redirect(url_for("index"))

    signup_flag = True
    message = page_name
    header_bg = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        signup_flag = False
        if not (username and password and email):
            message = "Username, Password and Email are required"
        elif users.find_one({"username": username}):
            message = "Username already taken"
        elif users.find_one({"email": email}):
            message = "Email already in use"
        else:
            try:
                users.insert_one(
                    {
                        "username": username,
                        "password": password,
                        "email": email,
                    }
                )
                signup_flag = True
                message = username
            except Exception as error:
                message = type(error).__name__

        if signup_flag:
            session["signup_to_signin"] = True
            return redirect(url_for("signin"))

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

    if check_auth("token", app.secret_key):
        return redirect(url_for("index"))

    js = False
    header_bg = ""
    message = page_name

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users.find_one({"username": username})

        if user and (user["password"] == password):
            encrypted_username = encrypt(username, app.secret_key)
            session["signin_to_index"] = True
            response = redirect(url_for("index"))
            response.set_cookie("token", encrypted_username, max_age=7200)
            return response

        message = "Invalid credentials"
        header_bg = "error-bg"

    signup_to_signin = session.pop("signup_to_signin", False)
    if signup_to_signin:
        js = True
        header_bg = "success-bg"
        message = "Your account created successfully"

    signout_to_signin = session.pop("signout_to_signin", False)
    send_to_signin = session.pop("send_to_signin", False)
    sent_to_signin = session.pop("sent_to_signin", False)
    inbox_to_signin = session.pop("inbox_to_signin", False)
    if signout_to_signin or send_to_signin or sent_to_signin or inbox_to_signin:
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
    if not check_auth("token", app.secret_key):
        session["signout_to_signin"] = True
        return redirect(url_for("signin"))

    session["signout_to_index"] = True
    response = redirect(url_for("index"))
    response.set_cookie("token", "", expires=0)
    return response


@app.route("/inbox/")
def inbox():
    page_name = "Inbox"

    username = check_auth("token", app.secret_key)
    if not username:
        session["inbox_to_signin"] = True
        return redirect(url_for("signin"))

    js = False
    header_bg = ""
    message = page_name

    page_number = request.args.get("page", 1)
    if not page_number:
        page_number = 1
    page_number = int(page_number)
    skip = (page_number - 1) * PAGE_SIZE

    pipeline = [
        {"$match": {"to": username}},
        {"$project": {"from": 1, "date": 1, "time": 1, "subject": 1, "body": 1}},
        {"$sort": {"date": -1, "time": -1}},
        {"$skip": skip},
        {"$limit": PAGE_SIZE},
    ]
    received_emails = emails.aggregate(pipeline)

    received_emails_list = []
    for email in received_emails:
        email_data = {
            "from": email["from"],
            "date": email["date"],
            "time": email["time"],
            "subject": email["subject"],
            "body": email["body"],
        }
        received_emails_list.append(email_data)

    data = received_emails_list
    there_is_next_page = len(data) == PAGE_SIZE

    return render_template(
        "inbox.html",
        js=js,
        message=message,
        header_bg=header_bg,
        page_name=page_name,
        username=username,
        data=data,
        page_number=page_number,
        there_is_next_page=there_is_next_page,
    )


@app.route("/sent/")
def sent():
    page_name = "Sent"

    username = check_auth("token", app.secret_key)
    if not username:
        session["sent_to_signin"] = True
        return redirect(url_for("signin"))

    js = False
    header_bg = ""
    message = page_name

    send_to_sent = session.pop("send_to_sent", False)
    if send_to_sent:
        js = True
        header_bg = "success-bg"
        message = "Email sent"

    page_number = request.args.get("page", 1)
    if not page_number:
        page_number = 1
    page_number = int(page_number)
    skip = (page_number - 1) * PAGE_SIZE

    pipeline = [
        {"$match": {"from": username}},
        {"$project": {"to": 1, "date": 1, "time": 1, "subject": 1, "body": 1}},
        {"$sort": {"date": -1, "time": -1}},
        {"$skip": skip},
        {"$limit": PAGE_SIZE},
    ]
    sent_emails = emails.aggregate(pipeline)

    sent_email_list = []
    for email in sent_emails:
        email_data = {
            "to": email["to"],
            "date": email["date"],
            "time": email["time"],
            "subject": email["subject"],
            "body": email["body"],
        }
        sent_email_list.append(email_data)

    data = sent_email_list
    there_is_next_page = len(data) == PAGE_SIZE

    return render_template(
        "sent.html",
        js=js,
        message=message,
        header_bg=header_bg,
        page_name=page_name,
        username=username,
        data=data,
        page_number=page_number,
        there_is_next_page=there_is_next_page,
    )


@app.route("/send/", methods=["GET", "POST"])
def send():
    page_name = "Send"

    username = check_auth("token", app.secret_key)
    if not username:
        session["send_to_signin"] = True
        return redirect(url_for("signin"))

    js = False
    header_bg = ""
    message = page_name

    if request.method == "POST":
        to = request.form.get("to")
        subject = request.form.get("subject")
        body = request.form.get("body")

        if not (to and subject and body):
            header_bg = "error-bg"
            message = "Username, Subject and Body are required"
        else:
            error_in_insertion = False
            if users.find_one({"email": to}):
                try:
                    emails.insert_one(
                        {
                            "from": username,
                            "to": to,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "subject": subject,
                            "body": body,
                        }
                    )
                except Exception as error:
                    js = True
                    header_bg = "error-bg"
                    message = type(error).__name__
                    error_in_insertion = True
            else:
                js = True
                header_bg = "error-bg"
                message = "Email does not exist"
                error_in_insertion = True

            if not error_in_insertion:
                session["send_to_sent"] = True
                return redirect(url_for("sent"))

    return render_template(
        "send.html",
        js=js,
        message=message,
        header_bg=header_bg,
        page_name=page_name,
        username=username,
    )


@app.route("/toastr")
def toastr():
    return render_template("toastr.html")


if __name__ == "__main__":
    app.run(debug=True)
