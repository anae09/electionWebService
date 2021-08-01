from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy();


class ElectionParticipant(database.Model):
    __tablename__ = "electionparticipant";
    id = database.Column(database.Integer, primary_key=True);
    idParticipant = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable=False);
    idElection = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False);
    pollNumber = database.Column(database.Integer, nullable=False);
    # votes = database.relationship("Vote", back_populates="electionParticipant");
    participant = database.relationship("Participant", back_populates="electionInfo");

    def toJSON(self):
        return {
            "pollNumber": self.pollNumber,
            "name": self.participant.name
        }


class Participant(database.Model):
    __tablename__ = "participants";
    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256), nullable=False);
    individual = database.Column(database.Boolean, nullable=False);
    elections = database.relationship("Election", secondary=ElectionParticipant.__table__,
                                      back_populates="participants");
    electionInfo = database.relationship("ElectionParticipant", back_populates="participant");

    def __repr__(self):
        return '{{ id: {}, name: {}, individual: {}}}'.format(self.id, self.name, self.individual);

    def participantJSON(self, allFields=True):
        if not allFields:
            return {"id": self.id, "name": self.name};
        return {"name": self.name, "individual": self.individual, "id": self.id};


class Election(database.Model):
    __tablename__ = "elections";
    id = database.Column(database.Integer, primary_key=True);
    start = database.Column(database.DateTime, nullable=False);
    end = database.Column(database.DateTime, nullable=False);
    individual = database.Column(database.Boolean, nullable=False);
    participants = database.relationship("Participant", secondary=ElectionParticipant.__table__,
                                         back_populates="elections");
    votes = database.relationship("Vote", backref="election", lazy=True);

    def electionJSON(self):
        return {"id": self.id, "start": self.start.isoformat(), "end": self.end.isoformat(),
                "individual": self.individual,
                "participants": [p.participantJSON(allFields=False) for p in self.participants],
                "votes": [v.toJSON() for v in self.votes]};

    def __repr__(self):
        return '{{"id": {}, "start": {}, "end": {}, "individual": {}, "participants": [{}]}}'.format(self.id,
                                                                                                     self.start,
                                                                                                     self.end,
                                                                                                     self.individual,
                                                                                                     self.participants);


class Vote(database.Model):
    __tablename__ = "votes";
    id = database.Column(database.Integer, primary_key=True);
    valid = database.Column(database.Boolean, nullable=False);
    ballotGuid = database.Column(database.String(256), nullable=False);
    reason = database.Column(database.Text, nullable=False);
    officialJMBG = database.Column(database.String(13), nullable=False);
    pollNumber = database.Column(database.Integer);
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False);

    # electionParticipant = database.relationship("ElectionParticipant", back_populates="votes");

    def toJSON(self):
        return {
            "ballotGuid": self.ballotGuid,
            "electionOfficialJmbg": self.officialJMBG,
            "pollNumber": self.pollNumber,
            "reason": self.reason
        }

    def __repr__(self):
        return '{{ "electionOfficialJmbg": {}, "ballotGuid": {}, "pollNumber": {}, "reason": {}}}'.format(
            self.officialJMBG, self.ballotGuid, self.pollNumber, self.reason);
