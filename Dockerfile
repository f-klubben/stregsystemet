FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# Write local.cfg from env vars at startup
CMD sh -c "printf '[database]\nengine=django.db.backends.postgresql\nname=${POSTGRES_DB}\nuser=${POSTGRES_USER}\npassword=${POSTGRES_PASSWORD}\nhost=${POSTGRES_HOST}\nport=5432\n' > local.cfg && \
    python manage.py collectstatic --noinput && \
    gunicorn stregsystem.wsgi:application --bind 0.0.0.0:8080"