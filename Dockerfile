FROM python:3.11
WORKDIR /accesser

RUN pip install -U "accesser[doh,doq]"

EXPOSE 7654
VOLUME /accesser

CMD ["accesser"]
