# yandexvision
1.создать сервисный аккаунт с ролями editor, serverless.functions.invoker

2.сгенерировать ключи доступа и API ключи к аккаунту

3.создать бакет itis-2022-2023-vvot15-photos

4.создать к нему триггер vvot15-photo-trigger, запускающий функцию vvot15-face-detection, когда в бакете появляется новый файл с суффиксом .jpg

5.в функцию скопировать код из vvot15-face-detection.py, в 47 строке вместо * подставить API ключ сервисного аккаунта

6.добавить переменные окружения AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

7.выбрать сервисный аккаунт созданный нами

8.создать очереть vvot15-tasks

to be continued...
