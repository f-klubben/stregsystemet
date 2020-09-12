#!/bin/bash

rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata stregsystem/fixtures/testdata-mobilepay.json
python manage.py runserver
