import base64
import io
import json
import os
import uuid
import boto3
import requests as r
from PIL import Image
from requests.structures import CaseInsensitiveDict


AWS_ACCESS_KEY_ID = os.environ.get('aws_access_key_id')
AWS_SECRET_ACCESS_KEY = os.environ.get('aws_secret_access_key')


def main(event, context):
    bucket_id = event['messages'][0]['details']['bucket_id']
    object_id = event['messages'][0]['details']['object_id']

    session = boto3.session.Session()

    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    sqs = session.resource(
        service_name='sqs',
        endpoint_url='https://message-queue.api.cloud.yandex.net',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name='ru-central1'
    )

    message_queue = sqs.get_queue_by_name(QueueName='vvot15-tasks')
    s3_response_object = s3.get_object(Bucket=bucket_id, Key=object_id)
    object_content = s3_response_object['Body'].read()
    encoded_object = base64.b64encode(object_content)

    request_json = json.dumps(
        {"folderId" : "b1ghca532kcodcg8p092", "analyze_specs": [{"content": encoded_object.decode('ascii'), "features": [{"type": "FACE_DETECTION"}]}]},
        indent=4
    )

    authorization_headers = CaseInsensitiveDict()
    authorization_headers["Authorization"] = "Api-Key *"
    authorization_headers["Content-Type"] = "application/json"
    faces_response = r.post(
        "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze",
        headers=authorization_headers,
        data=request_json
    )
    faces_response_json = faces_response.json()

    try:
        faces_json = faces_response_json['results'][0]['results'][0]['faceDetection']['faces']
        for (index, face) in enumerate(faces_json):
            coordinate_1 = face['boundingBox']['vertices'][0]
            coordinate_2 = face['boundingBox']['vertices'][2]
            message_queue.send_message(MessageBody='New_Face', MessageAttributes=
                {
                    'Parent_object' :
                    {
                        'DataType': 'String',
                        'StringValue': object_id
                    } ,
                    'upper_left_x' :
                    {
                        'DataType': 'String',
                        'StringValue': coordinate_1['x']
                    } ,
                    'upper_left_y' :
                    {
                        'DataType': 'String',
                        'StringValue': coordinate_1['y']
                    } ,
                    'lower_right_x' :
                    {
                        'DataType': 'String',
                        'StringValue': coordinate_2['x']
                    },
                    'lower_right_y' :
                    {
                        'DataType': 'String',
                        'StringValue': coordinate_2['y']
                    }                   
                })
        print(faces_response_json)
    except KeyError:
        return faces_response_json