import re
from flask import Flask, request, make_response, jsonify, Response;
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity;
from configuration import Configuration;
from models import database, User, Role, UserRole;

app = Flask(__name__);
app.config.from_object(Configuration);

jwt = JWTManager(app);

email_re = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b';
password_re = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$';


@app.route("/", methods=["GET", "POST"])
def index():
    return "<h1>Pocetna radi</h1>";


def calcK(jmbg):
    step = 6;
    n = 7;
    value = 0;
    try:
        for i in range(0, 6):
            value += n * (int(jmbg[i]) + int(jmbg[i + step]));
            n = n - 1;
    except ValueError:
        return -1;
    return 11 - value % 11;


def checkJMBG(jmbg):
    if len(jmbg) != 13:
        return -1;
    try:
        dd = int(jmbg[0:2]);
        mm = int(jmbg[2:4]);
        yyy = int(jmbg[4:7]);
        rr = int(jmbg[7:9]);
        bbb = int(jmbg[9:12]);
        if dd < 1 or dd > 31 or mm < 1 or mm > 12 or yyy < 0 or yyy > 999 or rr < 70 or rr > 99 or bbb < 0 or bbb > 999:
            return -1;
        k = int(jmbg[12]);
        m = calcK(jmbg);
        if 10 <= m <= 11:
            if k != 0:
                return -1;
        if 1 <= m <= 9:
            if k != m:
                return -1;
    except ValueError:
        return -1;
    return 1;


def checkFields(data):
    if "jmbg" not in data or len(data["jmbg"]) == 0:
        return make_response(jsonify(message="Field jmbg is missing."), 400);
    if "forename" not in data or len(data["forename"]) == 0:
        return make_response(jsonify(message="Field forename is missing."), 400);
    if "surname" not in data or len(data["surname"]) == 0:
        return make_response(jsonify(message="Field surname is missing."), 400);
    if "email" not in data or len(data["email"]) == 0:
        return make_response(jsonify(message="Field email is missing."), 400);
    if "password" not in data or len(data["password"]) == 0:
        return make_response(jsonify(message="Field password is missing."), 400);
    return "";


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json();
    status = checkFields(data);
    if status != "":
        return status;

    jmbg = request.json["jmbg"];
    if checkJMBG(jmbg) < 0:
        return make_response(jsonify(message="Invalid jmbg."), 400);

    forename = request.json["forename"];
    surname = request.json["surname"];

    email = request.json["email"];
    if len(email) > 256 or not re.match(email_re, email):
        return make_response(jsonify(message="Invalid email."), 400);

    password = request.json["password"];
    if len(password) > 256 or not re.match(password_re, password):
        return make_response(jsonify(message="Invalid password."), 400);

    res = User.query.filter(User.email == email).first();
    # print(str(res))
    if res:
        return make_response(jsonify(message="Email already exists."), 400);

    res = User.query.filter(User.jmbg == jmbg).first();
    # print(str(res));
    if res:
        return make_response(jsonify(message="JMBG already exists."), 400);
    try:
        user = User(forename=forename, surname=surname, jmbg=jmbg, email=email, password=password);
        database.session.add(user);
        database.session.commit();
    except IntegrityError:
        database.session.rollback();
        return "Unknown error adding user."

    userrole = UserRole(userId=user.id, roleId=2);  # role=zvanicnik
    database.session.add(userrole);
    database.session.commit();

    return Response(status=200);


@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "");
    if len(email) == 0:
        return make_response(jsonify(message="Field email is missing."), 400);

    password = request.json.get("password", "");
    if len(password) == 0:
        return make_response(jsonify(message="Field password is missing."), 400);

    if len(email) > 256 or not re.match(email_re, email):
        return make_response(jsonify(message="Invalid email."), 400);

    user = User.query.filter(and_(User.email == email, User.password == password)).first();

    if not user:
        return make_response(jsonify(message="Invalid credentials."), 400);

    additionalClaims = {
        "jmbg": user.jmbg,
        "forename": user.forename,
        "surname": user.surname,
        "password": user.password,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=email, additional_claims=additionalClaims);
    refreshToken = create_refresh_token(identity=email, additional_claims=additionalClaims);

    return make_response(jsonify({"accessToken": accessToken, "refreshToken": refreshToken}), 200);


@app.route("/check", methods=["POST", "GET"])
@jwt_required()
def check():
    return Response("Token is valid.", status=200);


@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity();
    refreshClaims = get_jwt();
    # print(identity, refreshClaims);
    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "password": refreshClaims["password"],
        "roles": refreshClaims["roles"]
    }
    accessToken = create_access_token(identity=identity, additional_claims=additionalClaims);
    return make_response(jsonify({"accessToken": accessToken}), 200);


@app.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    email = request.json.get("email", "");
    if len(email) == 0:
        return make_response(jsonify(message="Field email is missing."), 400);
    if len(email) > 256 or not re.match(email_re, email):
        return make_response(jsonify(message="Invalid email."), 400);

    user = User.query.filter(User.email == email).first();
    if not user:
        return make_response(jsonify(message="Unknown user."), 400);
    userrole = UserRole.query.filter(UserRole.userId == user.id).first();

    database.session.delete(userrole);
    database.session.commit();

    database.session.delete(user);
    database.session.commit();

    return Response(status=200);


@app.route("/allUsers", methods=["GET"])
def users():
    return str(User.query.all());


if __name__ == "__main__":
    database.init_app(app);
    app.run(debug=True, host="0.0.0.0", port=5001);
