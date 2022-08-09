# Use an official Python runtime based on Debian 10 "buster" as a parent image.
FROM python:3.9-slim

RUN python -m pip install --upgrade pip

# remove root user dependency

RUN addgroup --system app && adduser --system --group app

USER app

ENV HOME /home/app

# Устанавливаем зависимости проекта
ENV PATH="$PATH:$HOME/.local/bin"
COPY ./requirements.txt $HOME
RUN pip install --upgrade pip
RUN pip install --user app -r $HOME/requirements.txt

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
ENV PYTHONUNBUFFERED=1

# Copy the source code of the project into the container.
COPY --chown=app:app *.py $HOME/
WORKDIR $HOME

ENTRYPOINT python worker.py
