from redis import Redis;
import json;
from configuration import Configuration;
from models import database, Election, ElectionParticipant, Participant, Vote;
import datetime;
from sqlalchemy import and_;
from flask import Flask;

app = Flask(__name__);
app.config.from_object(Configuration);

pollNumbers = [];
guids = [];


def checkVotes():
    with app.app_context():
        done = False;
        while not done:
            try:
                elections = Election.query.all();
                done = True;
            except Exception as err:
                print(err);
    # print("Check votes");
    with app.app_context():
        with Redis(host=Configuration.REDIS_HOST, port=6379) as redis:
            activeElection = None;
            # elections = Election.query.all();
            # print(elections);
            while True:
                _, content = redis.blpop(Configuration.REDIS_VOTES_LIST);
                timestamp = datetime.datetime.now().replace(microsecond=0);
                print("now:", timestamp);
                if not activeElection or not activeElection.start <= timestamp <= activeElection.end:
                    database.session.commit();
                    elections = Election.query.all();
                    # print(elections);
                    pollNumbers.clear();
                    guids.clear();
                    for e in elections:
                        if e.start <= timestamp <= e.end:
                            activeElection = e;
                            pollNumbersDB = ElectionParticipant.query.filter(ElectionParticipant.idElection == activeElection.id).all();
                            for row in pollNumbersDB:
                                pollNumbers.append(row.pollNumber);
                            print(pollNumbersDB);
                            break;
                if not activeElection:
                    print("No active election, vote discarded");
                    continue;
                # print(activeElection);

                voteInfo = content.decode("utf-8");
                voteData = json.loads(voteInfo);
                # print(voteData);
                reason = "";
                valid = True;
                # duplicateGuid = Vote.query.filter(Vote.ballotGuid == voteData["guid"]).first();
                # if duplicateGuid:
                #    reason = "Duplicate ballot.";
                if voteData["guid"] in guids:
                    reason = "Duplicate ballot.";
                else:
                    guids.append(voteData["guid"]);
                # invalidPollNumber = ElectionParticipant.query.filter(
                #    and_(ElectionParticipant.idElection == activeElection.id, ElectionParticipant.pollNumber
                #         == voteData["pollNumber"])).first();
                # if not invalidPollNumber:
                #    reason = "Invalid poll number.";
                if voteData["pollNumber"] not in pollNumbers:
                    reason = "Invalid poll number.";
                if len(reason) > 0:
                    valid = False;
                vote = Vote(valid=valid, ballotGuid=voteData["guid"], reason=reason, pollNumber=voteData["pollNumber"],
                            officialJMBG=voteData["officialJMBG"], electionId=activeElection.id);
                # print(vote);
                database.session.add(vote);
                database.session.commit();


if __name__ == "__main__":
    database.init_app(app);
    checkVotes();
