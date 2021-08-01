FROM python:3

RUN mkdir -p /opt/src/votingstation
WORKDIR /opt/src/votingstation

COPY applications/officials/official.py ./official.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/votingstation"

ENTRYPOINT ["python", "./official.py"]