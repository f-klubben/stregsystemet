Stregsystemet [![Django CI Actions Status](https://github.com/f-klubben/stregsystemet/workflows/Django%20CI/badge.svg)](https://github.com/f-klubben/stregsystemet/actions)  [![codecov](https://codecov.io/gh/f-klubben/stregsystemet/branch/next/graph/badge.svg)](https://codecov.io/gh/f-klubben/stregsystemet) 
========

This is the current stregsystem in the F-Klub.

Branches
-------
 - `master`: The running code on the live system.
 - `next`: The set of changes which will be included in the next release.

Python Environment
-------
For windows using Anaconda and virtual environments:
1. Download and install Anaconda
2. In a shell:
  - `conda create -n stregsystem python=3.6`
  - `activate stregsystem`
  - `pip install -r requirements.txt`
3. ???
4. Profit

For Ubuntu with virtual envs:
1. Install python3 with pip
 - `sudo apt install python3 python3-pip`
2. Create virtual environment
 - `python3 -m venv venv`
3. Activate virtualenv
 - `source venv/bin/activate`
4. Install packages
 - `pip3 install -r requirements.txt`
5. ???
6. Profit

Using Testdata
--------
In order to simplify development for all, we have included a test fixture.
Using `testserver` will delete the data after running.
To use it do the following:
1. `python manage.py migrate`
2. `python manage.py testserver stregsystem/fixtures/testdata.json`
3. ???
4. Profit

Admin panel: <http://127.0.0.1:8000/admin/>  
Login: `tester:treotreo`

Stregsystem: <http://127.0.0.1:8000/1/>  
User: `tester`

Persistent Testdata
-------
Using `runserver` will automatically reload django on code change, and persist data in the database configured in `local.cfg` (can be whatever backend you want to use).
First time:
1. `python manage.py migrate`
2. `python manage.py loaddata stregsystem/fixtures/testdata.json`
3. `python manage.py runserver`
4. ???
5. Profit

From then on
1. `python manage.py runserver`
2. ???
3. Profit
