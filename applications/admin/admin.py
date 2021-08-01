from flask import Flask, request, jsonify, make_response;
from flask_jwt_extended import jwt_required, JWTManager
from sqlalchemy import func, and_
from configuration import Configuration;
from models import database, Participant, Election, ElectionParticipant, Vote;
from dateutil import parser
import datetime

app = Flask(__name__);
app.config.from_object(Configuration);

jwt = JWTManager(app);


@app.route("/", methods=["GET", "POST"])
def index():
    return "Admin page working!!!";


@app.route("/deleteAll", methods=["GET", "POST"])
def deleteAll():
    try:
        num_rows_deleted = database.session.query(ElectionParticipant).delete();
        database.session.commit();
        num_rows_deleted = database.session.query(Vote).delete();
        database.session.commit();
        num_rows_deleted = database.session.query(Election).delete();
        database.session.commit();
        num_rows_deleted = database.session.query(Participant).delete();
        database.session.commit();
        return make_response(jsonify(message="Delete all successful"), 200);
    except Exception as err:
        print(err);
        database.session.rollback();
    return make_response(jsonify(message="Delete all not successful"), 200);


@app.route("/createParticipant", methods=["POST"])
@jwt_required()
def createParticipant():
    data = request.get_json();
    if "name" not in data or len(data["name"]) == 0:
        return make_response(jsonify(message="Field name is missing."), 400);
    if "individual" not in data:
        return make_response(jsonify(message="Field individual is missing."), 400);

    name = data["name"];
    individual = data["individual"];

    participant = Participant(name=name, individual=individual);
    database.session.add(participant);
    database.session.commit();

    return make_response(jsonify(id=participant.id), 200);


@app.route("/getParticipants", methods=["GET"])
@jwt_required()
def getParticipants():
    participants = Participant.query.all();
    participantsList = [p.participantJSON() for p in participants];
    message = jsonify(participants=participantsList);
    return make_response(message, 200);


def checkElectionFields(data):
    if "start" not in data or len(data["start"]) == 0:
        return make_response(jsonify(message="Field start is missing."), 400);
    if "end" not in data or len(data["end"]) == 0:
        return make_response(jsonify(message="Field end is missing."), 400);
    if "individual" not in data:
        return make_response(jsonify(message="Field individual is missing."), 400);
    if "participants" not in data:
        return make_response(jsonify(message="Field participants is missing."), 400);
    return "";


# checks if there is an election with overlapping period; return true if there is
def validElectionPeriod(start, end):
    allElections = Election.query.filter().all();
    print(start, end);
    for election in allElections:
        if (election.start <= start <= election.end) or (election.start <= end <= election.end) or (
                start <= election.start and end >= election.end):
            return False;
    return True;


def validElectionParticipants(presidentElection, participants):
    for pid in participants:
        if type(pid) is not int:
            return False;
        participant = Participant.query.get(pid);
        print(str(participant));
        if not participant:
            return False;
        if (participant.individual and not presidentElection) or (not participant.individual and presidentElection):
            return False;
    return True;


@app.route("/createElection", methods=["POST"])
@jwt_required()
def createElection():
    data = request.get_json();
    status = checkElectionFields(data);
    if status != "":
        return status;
    try:
        start = parser.isoparse(data["start"]).replace(tzinfo=None);
        end = parser.isoparse(data["end"]).replace(tzinfo=None);
        if start >= end or not validElectionPeriod(start, end):
            raise ValueError
    except ValueError:
        return make_response(jsonify(message="Invalid date and time."), 400);

    individual = data["individual"];
    participants = data["participants"];

    if len(participants) < 2 or not validElectionParticipants(individual, participants):
        return make_response(jsonify(message="Invalid participants."), 400);

    election = Election(start=start, end=end, individual=individual);
    database.session.add(election);
    database.session.commit();

    for i in range(0, len(participants)):
        electionparticipant = ElectionParticipant(idParticipant=participants[i], idElection=election.id,
                                                  pollNumber=(i + 1));
        database.session.add(electionparticipant);
        database.session.commit();

    return make_response(jsonify(pollNumbers=[(i + 1) for i in range(0, len(participants))]), 200)


@app.route("/getElections", methods=["GET"])
@jwt_required()
def getElections():
    allElections = Election.query.all();
    return make_response(jsonify(elections=[e.electionJSON() for e in allElections]), 200);


def presidentElectionResults(electionId, electionData):
    participants = [];
    totalVotes = Vote.query.filter(and_(Vote.electionId == electionId, Vote.valid == 1)).count();
    print("Total votes:", totalVotes);
    if totalVotes == 0:
        return [];
    sumVotes = Vote.query.filter(and_(Vote.electionId == electionId, Vote.valid == 1)).group_by(
        Vote.pollNumber).with_entities(Vote.pollNumber,
                                       func.count());
    for e in electionData:
        p = e.toJSON();
        print(p);
        d = {
            "pollNumber": p["pollNumber"],
            "name": p["name"],
            "result": round((sumVotes.filter(Vote.pollNumber == p["pollNumber"]).first()[1] * 1.0 / totalVotes), 2)
        }
        participants.append(d);
    return participants;


def dformula(votes, seats):
    return votes / (2 * seats + 1);


total_seats = 250;


def parliamentElectionResults(electionId, electionData):
    participants = [];
    totalVotes = Vote.query.filter(and_(Vote.electionId == electionId, Vote.valid == 1)).count();
    print("Total votes:", totalVotes);
    if totalVotes == 0:
        return [];
    threshold = float(totalVotes * 0.05);
    print("***CENZUS:", threshold);
    sumVotes = Vote.query.filter(and_(Vote.electionId == electionId, Vote.valid == 1)).group_by(
        Vote.pollNumber).with_entities(Vote.pollNumber,
                                       func.count());
    party_votes = dict();
    party_seats = dict();
    for row in sumVotes:
        if row[1] >= threshold:
            party_votes[row[0]] = row[1];
            party_seats[row[0]] = 0;
    # print("party_votes", party_votes);
    # print("party_seats", party_seats);

    for i in range(0, total_seats):
        iter_result = [];
        for p in party_votes:
            q = (party_votes[p]) / (2 * party_seats[p] + 1);
            iter_result.append((q, p));
        iter_result.sort(reverse=True);
        # print(iter_result);
        party_seats[iter_result[0][1]] += 1;
        # print(party_seats);

    for e in electionData:
        p = e.toJSON();
        if p["pollNumber"] in party_votes:
            result = party_seats[p["pollNumber"]];
        else:
            result = 0;
        d = {
            "pollNumber": p["pollNumber"],
            "name": p["name"],
            "result": result
        }
        print(d);
        participants.append(d);

    return participants;


@app.route("/getResults", methods=["GET"])
@jwt_required()
def getResults():
    electionId = request.args.get("id");
    if not electionId:
        return make_response(jsonify(message="Field id is missing."), 400);
    election = Election.query.get(electionId);
    print("Selected election:", election);
    if not election:
        return make_response(jsonify(message="Election does not exist."), 400);
    if datetime.datetime.now() <= election.end:
        return make_response(jsonify(message="Election is ongoing."), 400);

    electionData = ElectionParticipant.query.join(Participant).filter(
        ElectionParticipant.idElection == electionId).all();

    database.session.commit();
    invalidVotes = [];
    if election.individual:
        participants = presidentElectionResults(electionId, electionData);
    else:
        participants = parliamentElectionResults(electionId, electionData);

    invalidVotesData = Vote.query.filter(and_(Vote.electionId == electionId, Vote.valid == 0)).all();
    for v in invalidVotesData:
        invalidVotes.append(v.toJSON());

    return make_response(jsonify(participants=participants, invalidVotes=invalidVotes), 200);


if __name__ == "__main__":
    database.init_app(app);
    app.run(debug=True, host="0.0.0.0", port=5002);
