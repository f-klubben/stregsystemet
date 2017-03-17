Branches
-------
 - `master`: The running code on the live system.
 - `next`: The set of changes which will be included in the next release.
 - Any other: Dunno.

Using Testdata
--------
1. `python manage.py migrate`
2. `python manage.py testserver stregsystem/fixtures/testdata.json`
3. ???
4. Profit

Admin panel: `http://127.0.0.1:8000/admin/` Login: tester:treotreo
Stregsystem: `http://127.0.0.1:8000/1/` User: tester
