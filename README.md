# Election Process Management Web Service

School project implemented using Python programming language and Flask and SQLAlchemy libraries.
There are also Docker Image templates which represent parts of the system and can be used for running Docker Containers.
User authentication utilizes JSON Web Tokens.

For running this web service:
>> Open project in Pycharm
>> Add Configuration -> Type: Docker Image -> foreach dockerfile (admin.dockerfile, authentication.dockerfile, authenticationDBmigration.dockerfile,
daemon.dockerfile, electionDBmigration.dockerfile, votingstation.dockerfile)
>> Add Configuration -> Type: Docker-Compose -> deployment.yaml
>> Run deployment

## Description

Web service which enables users to register participants (political party or individual), create and run election, and fetch election results.
There are two parts of the system, one for the user authentication and the other for running elections.

### User Authentication

1. User Registration
  URL: /register
  Type: POST
  Body: JSON of given format
    {
      "jmbg": "...",
      "forename": "...",
      "surname": "...",
      "email": "...",
      "password": "..."
    }

2. Login
  URL: /login
  Type: POST
  Body: JSON of given format
    {
      "email": "...",
      "password": "..."
    }
    
 3. Refresh Access Token
