from flask import Flask, request, make_response, Response, jsonify;
from flask_jwt_extended import jwt_required, get_jwt, JWTManager
from redis import Redis;
import io
import csv
import json
from configuration import Configuration;
from models import database;

app = Flask(__name__);
app.config.from_object(Configuration);

jwt = JWTManager(app);


@app.route("/", methods=["GET", "POST"])
def index():
    return "Officials page working";


@app.route("/vote", methods=["POST"])
@jwt_required()
def vote():
    if not request.files or "file" not in request.files or not request.files["file"]:
        return make_response(jsonify(message="Field file is missing."), 400);
    content = request.files["file"].stream.read().decode("utf-8");
    stream = io.StringIO(content);
    reader = csv.reader(stream);
    voteList = [];
    officialJMBG = get_jwt()["jmbg"];
    with Redis(host=Configuration.REDIS_HOST, port=6379) as redis:
        i = 0;
        for row in reader:
            if len(row) != 2:
                return make_response(jsonify(message=("Incorrect number of values on line {}.".format(i))), 400);
            try:
                voteData = {
                    "guid": row[0],
                    "pollNumber": int(row[1]),
                    "officialJMBG": officialJMBG
                }
                if voteData["pollNumber"] <= 0:
                    raise ValueError;
            except ValueError:
                return make_response(jsonify(message=("Incorrect poll number on line {}.".format(i))), 400);
            voteList.append(voteData);
            i = i + 1;

        voteList.reverse();
        print(voteList);

        for voteData in voteList:
            redis.lpush(Configuration.REDIS_VOTES_LIST, json.dumps(voteData));

    return Response(status=200);


if __name__ == "__main__":
    database.init_app(app);
    app.run(debug=True, host="0.0.0.0", port=5003);
