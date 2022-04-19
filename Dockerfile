FROM python:3.9
LABEL maintainer "Denise Sato <denise.vecino@gmail.com>"
WORKDIR /app

RUN apt-get update \
    && apt-get -y install graphviz-dev

RUN pip install -U numpy

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY ./ ./

EXPOSE 8050
CMD ["python", "index.py"]
# Used for heroku web server
#CMD ["gunicorn", "index:server"]
