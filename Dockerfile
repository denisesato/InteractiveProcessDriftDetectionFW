FROM python:3.7
#FROM heroku/heroku:20
LABEL maintainer "Denise Sato <denise.vecino@gmail.com>"
WORKDIR /app

#RUN apt-get update \
#    && apt-get -y install graphviz-dev

RUN apt-get update \
    && apt-get install -y --print-uris graphviz | grep http | awk '{print $1}' | tr -d "'"

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY ./ ./

EXPOSE 8050
CMD ["python", "index.py"]