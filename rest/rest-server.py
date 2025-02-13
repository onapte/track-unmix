import os
import json
import base64
import redis
from flask import Flask, request, jsonify, send_file
from io import BytesIO
import uuid
from minio import Minio

app = Flask(__name__)

redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

r = redis.StrictRedis(host=redisHost, port=redisPort, db=0, decode_responses=True)
SEPARATED_TRACKS_DIR = "separated_tracks"
if not os.path.exists(SEPARATED_TRACKS_DIR):
    os.makedirs(SEPARATED_TRACKS_DIR)

minioHost = os.getenv("MINIO_HOST") or "localhost:9000"

minio_client = Minio(
    minioHost,
    access_key="rootuser",
    secret_key="rootpass123",
    secure=False
)

INPUT_BUCKET_NAME = "in-audio-files"
OUTPUT_BUCKET_NAME = "out-audio-files"

if not minio_client.bucket_exists(INPUT_BUCKET_NAME):
    minio_client.make_bucket(INPUT_BUCKET_NAME)

if not minio_client.bucket_exists(OUTPUT_BUCKET_NAME):
    minio_client.make_bucket(OUTPUT_BUCKET_NAME)

@app.route("/", methods=['GET'])
def apiTest():
    return "<h1>Welcome to the Music Separation Server</h1>"

@app.route("/apiv1/separate", methods=['POST'])
def separate():
    try:
        data = request.get_json()
        callback_data = data.get('callback', {})

        if not data or 'mp3' not in data:
            return jsonify({"error": "No MP3 data found"}), 400

        mp3_base64 = data['mp3'].encode('utf-8')
        file_hash = str(uuid.uuid4())

        mp3_bytes = base64.b64decode(mp3_base64)
        mp3_filename = f"{file_hash}.mp3"
        mp3_bytes_io = BytesIO(mp3_bytes)

        minio_client.put_object(
            INPUT_BUCKET_NAME,
            mp3_filename,
            mp3_bytes_io,
            length=len(mp3_bytes)
        )

        print(f"Success: {mp3_filename} file uploaded to MinIO")

        file_data = {
            'hash': file_hash,
            'callback': callback_data
        }

        r.rpush('toWorker', json.dumps(file_data))

        response = {
            "hash": file_hash,
            "reason": "Song enqueued for separation"
        }
        
        return response, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/apiv1/queue", methods=['GET'])
def queue():
    queue_data = r.lrange("toWorker", 0, -1)
    return jsonify({"queue": queue_data})

@app.route("/apiv1/track/", methods=['GET'])
def get_track():
    data = request.args.to_dict()
    file_hash = data['hash']
    file_track = data['track']

    file_to_search = f'{file_hash}_{file_track}.mp3'
    minio_client.fget_object(OUTPUT_BUCKET_NAME, file_to_search, file_to_search)

    return send_file(file_to_search, as_attachment=True)

@app.route("/apiv1/remove/", methods=['GET'])
def remove_track():
    data = request.args.to_dict()
    file_hash = data['hash']

    if minio_client.bucket_exists(OUTPUT_BUCKET_NAME):
        files = list(map(lambda x : x.object_name, minio_client.list_objects(OUTPUT_BUCKET_NAME)))

        for file in files:
            if file_hash in file:
                minio_client.remove_object(OUTPUT_BUCKET_NAME, file)
                                           
        return jsonify({"status": "success", "message": "tracks removed"}), 200
    
    else:
        return jsonify({"status": "success", "message": "tracks do not exist"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)