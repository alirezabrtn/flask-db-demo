FROM python:3.9
WORKDIR /flask-db-demo
COPY /app /flask-db-demo/app
COPY /migrations /flask-db-demo/migrations
COPY requirements.txt /flask-db-demo/requirements.txt
RUN pip install -r requirements.txt
CMD bash -c "flask db upgrade && flask --debug run"

