Stregsystemet [![Build Status](https://travis-ci.org/f-klubben/stregsystemet.svg?branch=next)](https://travis-ci.org/f-klubben/stregsystemet)
========

This is the current stregsystem in the F-Klub.

Branches
-------
 - `master`: The running code on the live system.
 - `next`: The set of changes which will be included in the next release.

Using Testdata
--------
In order to simplify development for all, we have included a test fixture.
To use it do the following:
1. `python manage.py migrate`
2. `python manage.py testserver stregsystem/fixtures/testdata.json`
3. ???
4. Profit

Admin panel: `http://127.0.0.1:8000/admin/` 
Login: tester:treotreo

Stregsystem: `http://127.0.0.1:8000/1/` 
User: tester
