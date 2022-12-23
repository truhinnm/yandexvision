import json
import requests
import os
import ydb
import io
import boto3

driver = ydb.Driver(endpoint=os.getenv('YDB_ENDPOINT'), database=os.getenv('YDB_DATABASE'))
driver.wait(fail_fast=True, timeout=5)
pool = ydb.SessionPool(driver)

session = boto3.session.Session(region_name='ru-central1')
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net')

def get_face(session):
    return session.transaction().execute(
        f'SELECT face_key from faces where face_name is null;',
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )

text = ""
def main(event, context):
    request_body = json.loads(event['body'])
    request_text = ""
    try:
        request_text = request_body['message']['text']
    except:
        response_body = {
            "method": "sendMessage",
            "chat_id": request_body['message']['chat']['id'],
            "text": "Ошибка"
        };

    try:
        if request_body['message']['reply_to_message']['caption'] is not None:
            face = request_body['message']['reply_to_message']['caption']
            name = request_body['message']['text']

            def add_name(session):
                return session.transaction().execute(
                    f'UPDATE faces SET face_name=\"{name}\" WHERE face_key=\"{face}\";',
                    commit_tx=True,
                    settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
                )

            pool.retry_operation_sync(add_name)
            response_body = {
                "method": "sendMessage",
                "chat_id": request_body['message']['chat']['id'],
                "text": "Имя лица успешно изменено"
            };

    except:
        if request_text == "/getface":
            try:
                key = str(pool.retry_operation_sync(get_face)[0].rows[0].face_key)[2:-1]
                photo = f"{os.getenv('API_GATEWAY')}/?face={key}"
                response_body = {
                    "method": "sendPhoto",
                    "chat_id": request_body['message']['chat']['id'],
                    "photo": photo,
                    "caption": key
                };
            except:
                response_body = {
                    "method": "sendMessage",
                    "chat_id": request_body['message']['chat']['id'],
                    "text": "У всех лиц есть имена"
                };


        elif request_text.startswith("/find"):
            try:
                name = "".join(request_text.split("/find ")[1:])

                def get_photos(session):
                    return session.transaction().execute(
                        f'SELECT distinct original_key from faces where face_name=\"{name}\";',
                        commit_tx=True,
                        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
                    )

                photos_names = pool.retry_operation_sync(get_photos)[0].rows
                arr = []
                if len(photos_names) == 0:
                    response_body = {
                        "method": "sendMessage",
                        "chat_id": request_body['message']['chat']['id'],
                        "text": "Фото для этого имени не найдено"
                    };
                else:
                    for i in photos_names:
                        text = str(i.get('original_key'))[2:-1]
                        arr.append(
                            {"type": "photo",
                             "media": f"https://storage.yandexcloud.net/itis-2022-2023-vvot15-photos/{text}"})

                    response_body = {
                        "method": "sendMediaGroup",
                        "chat_id": request_body['message']['chat']['id'],
                        "media": arr
                    };
                if request_text == "/find":
                    text = "format: /find {name}"
                    response_body = {
                        "method": "sendMessage",
                        "chat_id": request_body['message']['chat']['id'],
                        "text": text
                    };
            except:
                text = "incorrect message format"
                response_body = {
                    "method": "sendMessage",
                    "chat_id": request_body['message']['chat']['id'],
                    "text": text
                };


        else:
            text = "Команды:\n /getface - Присылает фото с неопределенным лицом. Необходимо отправить имя\n /find {name} - Отправляет все фото с {name}."
            response_body = {
                "method": "sendMessage",
                "chat_id": request_body['message']['chat']['id'],
                "text": text
            };

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'isBase64Encoded': False,
        'body': json.dumps(response_body)
    }