import os
from sanic import Sanic
import io
import json

import boto3
from PIL import Image
import uuid
import ydb

import concurrent.futures

app = Sanic(__name__)

session = boto3.session.Session(region_name='ru-central1')
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net')

dr = None

def execute_query(session, face, original):
    session.transaction().execute(
        f"insert into face_table (face, name, orig) values (\"{face}\", null, \"{original}\");",
        commit_tx=True,
    )

@app.after_server_start
async def after_server_start(app, loop):
    print(f"App listening at port {os.environ['PORT']}")

@app.post("/")
async def main(request):
    body = json.loads(request.json['messages'][0]['details']['message']['attributes'])
    print(body)

    photo_object = io.BytesIO()
    s3.download_fileobj('itis-2022-2023-vvot15-photos', body['parent_object']['stringvalue'], photo_object)

    img = Image.open(photo_object)
    area = (int(body['upper_left_x']['stringvalue']), int(body['upper_left_y']['stringvalue']), int(body['lower_right_x']['stringvalue']), int(body['lower_right_y']['stringvalue']))
    cropped_img = img.crop(area)

    filename = str(uuid.uuid4())
    in_mem_file = io.BytesIO()
    cropped_img.save(in_mem_file, format="JPEG")
    in_mem_file.seek(0)
    s3.upload_fileobj(in_mem_file, 'itis-2022-2023-vvot15-faces', f"{filename}.jpg")

    print(3)
    execute_query(dr.table_client.session().create(), filename, body['photo'])
    print(4)
    return empty(status=200)

if __name__ == "__main__":
    driver_config = ydb.DriverConfig(
        'grpcs://ydb.serverless.yandexcloud.net:2135', os.getenv('YDB_DATABASE'),
        credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )
    with ydb.Driver(driver_config) as driver:
        try:
            driver.wait(timeout=10)
            dr = driver
        except concurrent.futures._base.TimeoutError:
            print("Connect failed to YDB")
            print("Last reported errors by discovery:")
            print(driver.discovery_debug_details())          
    app.run(host='0.0.0.0', port=int(os.environ['PORT']), motd=False, access_log=False)