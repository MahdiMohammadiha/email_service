from flask import Flask, render_template, url_for, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.email_service
users = db.users

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/signup/", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        signup_status = [False, "Not proceed."]

        username = request.form['username']
        password = request.form['password']

        try:
            if not (username and password):
                raise "Both Username and Ppassword must have value."
            users.insert_one({
                "username": username,
                "password": password
            })
            signup_status = [True, "Signup successful."]
        except Exception as error:
            signup_status = [False, type(error).__name__]
            
        print(signup_status[1])
        return redirect(url_for('index'))
    
    # all_users = users.find()
    return render_template("signup.html")
