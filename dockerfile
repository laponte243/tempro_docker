FROM python:3.12-slim-bullseye AS base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

RUN mkdir /app

WORKDIR /app
COPY . /app

RUN python3 -m venv /opt/venv

RUN /opt/venv/bin/pip install pip --upgrade

RUN /opt/venv/bin/pip install -r /app/requirements.txt

RUN chmod +x /app/msg-mqtt.py

CMD ["/opt/venv/bin/python", "/app/msg-mqtt.py"]