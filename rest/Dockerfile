FROM python:3.8-slim-buster

WORKDIR /app

RUN pip install flask requests redis minio jsonpickle

COPY rest-server.py /app

ENTRYPOINT [ "python", "rest-server.py"]