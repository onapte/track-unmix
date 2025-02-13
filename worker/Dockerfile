FROM xserrat/facebook-demucs:latest

WORKDIR /app

RUN pip install requests minio redis ffmpeg

COPY worker.py /app

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "worker.py"]