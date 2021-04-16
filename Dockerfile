FROM python:3.7
LABEL maintainer "Denise Sato <denise.vecino@gmail.com>"
WORKDIR /app

RUN apt-get update \
    && apt-get -y install graphviz-dev

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY ./ ./

EXPOSE 8050
#CMD ["python", "index.py"]
CMD ["gunicorn", "index:server"]
