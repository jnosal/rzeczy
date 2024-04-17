FROM python:3.11

RUN apt-get update && apt-get -y install tzdata software-properties-common netcat-traditional unzip gcc g++ make bash git build-essential python3.11-dev python3-pip
ENV TZ=Europe/Warsaw

RUN python3.11 -m pip install pip --upgrade && python3.11 -m pip install wheel

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

COPY . /usr/src/app

RUN groupadd -r nonroot
RUN useradd -g nonroot --no-create-home nonroot
RUN chown -R nonroot:nonroot /usr/src/app
USER nonroot

RUN chmod 777 docker-entrypoint.sh docker-testentrypoint.sh

EXPOSE 4444
