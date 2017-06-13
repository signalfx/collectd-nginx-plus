FROM python:2.7

ENV STATUS_CODES 100,200,300,400,500
ENV MIN_RESP_TIME 0
ENV MAX_RESP_TIME 500

ADD server.py ./
ADD requirements.txt ./

RUN pip install -r requirements.txt

EXPOSE 5000

CMD python server.py -s $STATUS_CODES -min $MIN_RESP_TIME -max $MAX_RESP_TIME
