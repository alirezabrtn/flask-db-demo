FROM python:3.10.16
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD flask db upgrade && flask run --debug