# Use an official Python runtime based on Debian 10 "buster" as a parent image.
FROM python:3.9-slim

ARG WORKERS
ARG PORT

RUN python -m pip install --upgrade pip

# remove root user dependency

RUN addgroup --system app && adduser --system --group app

USER app

ENV HOME /home/app

# Устанавливаем зависимости проекта
COPY ./requirements.txt $HOME
RUN pip install --user app -r $HOME/requirements.txt
ENV PATH="$PATH:$HOME/.local/bin"

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
ENV PYTHONUNBUFFERED=1

# Copy the source code of the project into the container.
COPY --chown=app:app *.py $HOME/
WORKDIR $HOME


ENV PORT=$PORT
ENV WORKERS=$WORKERS

ENTRYPOINT uvicorn --port $PORT --host 0.0.0.0 main:app --workers $WORKERS

HEALTHCHECK CMD curl --fail http://localhost:$PORT/stat || exit 1