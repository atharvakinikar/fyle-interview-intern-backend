FROM python:3.8

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=core/server.py

RUN rm -f core/store.sqlite3
RUN flask db upgrade -d core/migrations/

CMD ["bash", "run.sh"]