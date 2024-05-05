from itsdangerous import URLSafeTimedSerializer
from flask import request
from pymongo import MongoClient

client = MongoClient("localhost", 27017)
db = client.email_service
users = db.users
emails = db.emails


def encrypt(arg, secret_key):
    return URLSafeTimedSerializer(secret_key).dumps(arg)


def decrypt(arg, secret_key):
    return URLSafeTimedSerializer(secret_key).loads(arg)


def check_auth(cookie_name, secret_key):
    encrypted_username = request.cookies.get(cookie_name)
    response = False

    if encrypted_username:
        username = decrypt(encrypted_username, secret_key)
        if users.find_one({"username": username}):
            response = username

    return response
