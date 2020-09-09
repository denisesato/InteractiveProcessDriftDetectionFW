FROM python:3.7
LABEL maintainer "Denise Sato <denise.vecino@gmail.com>"
WORKDIR /code
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY ./ ./
EXPOSE 8050
CMD ["python", "./index.py"]