from flask import Flask, session, abort, redirect, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
import json
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager
import requests
from models import db, User
from config import SECRET_KEY, ABSTRACT_API_KEY
from flask import session as login_session
import json
from darija_API import ahlan_word, marhban_word
from arabic_API import arabic_greetings_first_lesson, arabic_alphabets_pronouciation


# Configure application
app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)
server_session = Session(app)


app.config['SECRET_KEY'] = SECRET_KEY
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flaskdb.db'
# Databse configuration  Mysql                            Username:password@hostname/databasename
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:''@localhost/flaskreact'

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

#################### Database Config ########################


jwt = JWTManager(app)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True
bcrypt = Bcrypt(app)
db.init_app(app)
with app.app_context():
    db.create_all()


# Limit the access to certain features
def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

#################### NORMAL Routes ########################


@app.route('/auth/login', methods=["POST"])
def create_token():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    user = User.query.filter_by(email=email).first()
    # if email != "test" or password != "test":
    #    return {"msg": "Wrong email or password"}, 401
    if user is None:
        return jsonify({"error": "Wrong email or passwords"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401

    access_token = create_access_token(identity=email)
    # response = {"access_token":access_token}

    return jsonify({
        "email": email,
        "access_token": access_token,
        "fullname": user.fullname
    })
    # return response


@app.route("/auth/signup", methods=["POST"])
def signup():
    email = request.json["email"]
    fullname = request.json["fullname"]
    password = request.json["password"]

    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
        return jsonify({"error": "Email already exists"}), 409

    api_key = f"https://emailvalidation.abstractapi.com/v1/?api_key={ABSTRACT_API_KEY}&email={email}"
    is_success = send_email_validation_request(api_key)
    if is_success and not user_exists:
        hashed_password = bcrypt.generate_password_hash(password)
        new_user = User(fullname=fullname, email=email,
                        password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            "id": new_user.id,
            "email": new_user.email,
            "fullname": new_user.fullname
        })
    else:
        return jsonify({"email": "The email is not valid"}), 409


def send_email_validation_request(key):
    try:
        # Do a request to the api
        response = requests.get(key)
        isValid = is_valid_email(response.content)
        # Check validity and act on it
        if isValid:
            return True
        else:
            return False
    # Raise expetion when something unusual happens
    except requests.exceptions.RequestException as api_error:
        print(
            f"There was an error contacting the Email Validation API: {api_error}")
        raise SystemExit(api_error)


def is_valid_email(APIresponseObject):
    data_values = []
    api_data = json.loads(APIresponseObject)
    for data in api_data:
        if "is" in data:
            data_values.append(api_data[data])

    # Get the values of the data returned from the api response
    is_valid_format = data_values[0]["value"]
    is_free_email = data_values[1]["value"]
    is_disposable_email = data_values[2]["value"]
    is_role_email = data_values[3]["value"]
    is_catchall_email = data_values[4]["value"]
    is_mx_found = data_values[5]["value"]
    is_smtp_valid = data_values[6]["value"]

    # Check the email if valid
    if is_valid_format and is_mx_found and is_smtp_valid and is_free_email:
        if not is_disposable_email and not is_role_email and not is_catchall_email:
            return True
        else:
            return False
    return False


@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response


@app.route("/logout")
def logout():
    session.clear()
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return redirect("/")

 # Arabic api responses


@app.route("/arabic/first-lesson")
def arabic_greetings():
    return arabic_greetings_first_lesson

    # Arabic letters responses


@app.route("/arabic/alphabets")
def arabic_alphabets():
    return arabic_alphabets_pronouciation

    # Darija api responses


@app.route("/darija/words/marhban")
def darija_words_marhban():
    return marhban_word


@app.route("/darija/words/ahlan")
def darija_words_ahlan():
    return ahlan_word


if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)
