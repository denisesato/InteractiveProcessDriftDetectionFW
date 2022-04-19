FROM python:3.9
LABEL maintainer "Denise Sato <denise.vecino@gmail.com>"
WORKDIR /app

RUN pip install -U numpy

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY ./ ./

EXPOSE 8050
#CMD ["python", "index.py"]
# Used for gunicorn web server
CMD ["gunicorn", "index:server"]
