FROM python:2.7

ENV TARGET_HOST localhost
ENV PORTS 80
ENV REQ_PER_SEC 1

ADD client.py ./
ADD requirements.txt ./

RUN pip install -r requirements.txt

CMD python client.py -d $TARGET_HOST -p $PORTS -r $REQ_PER_SEC
