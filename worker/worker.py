import os
import redis
from minio import Minio
import time
import json

redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

minioHost = os.getenv("MINIO_HOST") or "localhost:9000"

minio_client = Minio(
    minioHost,
    access_key="rootuser",
    secret_key="rootpass123", 
    secure=False
)

INPUT_BUCKET_NAME = "in-audio-files"
OUTPUT_BUCKET_NAME = "out-audio-files"

r = redis.StrictRedis(host=redisHost, port=redisPort, db=0, decode_responses=True)

INPUT_DIR = "/tmp/input"
OUTPUT_DIR = "/tmp/output"

if not os.path.exists(INPUT_DIR):
    os.makedirs(INPUT_DIR)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def get_file_path(file_hash):
    file_path = INPUT_DIR + '/' + f'{file_hash}.mp3'
    minio_client.fget_object(INPUT_BUCKET_NAME, f'{file_hash}.mp3', file_path)
    return file_path

def process_upload_file(file_path, file_name):
    operation = f"python -u -m demucs.separate -n mdx_extra_q --out {OUTPUT_DIR} {file_path} --mp3"
    os.system(operation)

    output_file_path = os.path.join(OUTPUT_DIR, 'mdx_extra_q', file_name[:-4])
    print(f'Saved separated tracks to {output_file_path}')

    for file in os.listdir(output_file_path):
        original_file_path = os.path.join(output_file_path, file)
        new_file_name = f'{file_name[:-4]}_{file}'

        new_file_path = os.path.join(output_file_path, new_file_name)
        os.rename(original_file_path, new_file_path)

    print(os.listdir(output_file_path))

    for file in os.listdir(output_file_path):
        print("Name of the file: ", file)
        tmp_file_path = os.path.join(output_file_path, file)
        minio_client.fput_object(
            OUTPUT_BUCKET_NAME,
            file,
            tmp_file_path
        )

        print(f"Success: Uploaded {file_name} to Min.IO bucket {OUTPUT_BUCKET_NAME}")
    
    print("All files uploaded!")


def worker_loop():
    while True:
        try:
            data = r.blpop("toWorker")
            parsed_data = json.loads(data[1])
            file_hash = parsed_data['hash']

            if file_hash:
                file_path = get_file_path(file_hash)
                process_upload_file(file_path, f'{file_hash}.mp3')
            else:
                time.sleep(1)
        except Exception as e:
            print(f"Error in worker loop: {e}")
            time.sleep(5)

if __name__ == '__main__':
    worker_loop()