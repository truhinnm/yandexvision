FROM ubuntu
RUN apt update && apt install -y python3 python3-pip
RUN pip3 install Pillow && pip3 install sanic && pip3 install ydb && pip3 install boto3 && pip3 install requests
RUN pip3 install ydb[yc]
COPY index.py /
COPY key.json /
CMD ["python3", "/index.py"]