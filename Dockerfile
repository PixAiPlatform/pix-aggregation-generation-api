FROM pixocial.azurecr.io/ai/ubuntu:22.04
#FROM alpine:3.13.5
WORKDIR /app
# RUN apt-get update


COPY ./bin ./bin
COPY ./config ./config
COPY ./plugins ./plugins
COPY ./run.sh ./run.sh
COPY ./requirements.txt ./requirements.txt

RUN apt update
RUN apt install -y python2.7-dev python3.10-dev netcat
RUN python3.10 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt
RUN chmod u+x ./bin/server_exec
RUN chmod u+x ./plugins/richpython3

CMD chmod u+x run.sh
ENTRYPOINT ["sh", "./run.sh"]
EXPOSE 8082
