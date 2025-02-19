FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y cron

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

COPY schedules /etc/cron.d/schedules

RUN chmod 0644 /etc/cron.d/schedules

RUN crontab /etc/cron.d/schedules

EXPOSE 8000

CMD cron && python manage.py runserver 0.0.0.0:8000