FROM python:3.9
LABEL maintainer "Denise Sato <denise.vecino@gmail.com>"
WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip install -U numpy

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY scikit-multiflow-0.6.dev0.tar.gz /
RUN pip install /scikit-multiflow-0.6.dev0.tar.gz

COPY ./ ./

EXPOSE 8050
#CMD ["python", "index.py"]
# Used for gunicorn web server
# CMD ["gunicorn", "index:server"]
ENTRYPOINT ["./gunicorn_starter.sh"]
