FROM python:3-slim
RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app
RUN python3 -m pip install -r requirements.txt

ADD . /app
ENTRYPOINT [ "gunicorn", "-b", "0.0.0.0:8000", "app:app" ]