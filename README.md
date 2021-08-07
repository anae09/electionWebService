# Election Process Management Web Service

School project implemented using Python programming language and Flask and SQLAlchemy libraries.
There are also Docker Image templates which represent parts of the system and can be used for running Docker Containers.
User authentication utilizes JSON Web Tokens.

To run this web service:
> Open project in Pycharm<br/>
> Add Configuration -> Type: Docker Image -> foreach dockerfile (set image tag to match the name in deployment.yaml)<br/>
> Add Configuration -> Type: Docker-Compose -> deployment.yaml<br/>
> Run deployment

stack.yaml is configured for cluster in Docker Swarm and development.yaml is configured for local testing.

## Description

Web service which enables users to register participants (political party or individual), create and run an election, and fetch election results.
There are two parts of the system, one for the user authentication and the other for running elections.

### User Authentication

User authentication part of the system consists of 3 docker images:
> authentication.dockerfile <br/>
> authenticationDBmigration.dockerfile -> for initial migration of authenticationDB; adds admin <br/>
> mysql image for authentication database

Available services:
* User Registration
* Login
* Refresh Access Token
* Delete User

### Election process management

Election process management part of the system consists of 4 docker images:
> admin.dockerfile <br/>
> votingstation.dockerfile <br/>
> daemon.dockerfile <br/>
> redis image for temporary storing of votes data <br/>
> mysql image for election database

Admin container provides services for:
* Creating participant
* Getting participants info
* Creating election
* Getting election list
* Getting election results

Voting station container provides service for officials and votes registration.<br/>
Information about votes is temporarily placed on Redis service.<br/>
Daemon service validates votes on Redis and saves data in the election database.
<br/><br/>
More information about available services in **IEP_PROJEKAT2021.pdf**.


