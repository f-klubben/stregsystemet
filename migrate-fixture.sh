### Example usage
# WARNING! Deletes your sqlite database
#
# `sh migrate-fixture.sh refactor/date-attribute stregsystem/fixtures/testdata.json`
# This will load the specified fixture on current `next` branch,
# then it switches to the specified branch, and migrates the database,
# then it dumps the database to the same file.
### 

# Setup load current test data
rm db.sqlite3.bak
mv db.sqlite3 db.sqlite3.bak
git switch next
python manage.py migrate
python manage.py loaddata $2

# Migrate test data
git switch $1
python manage.py migrate
python manage.py dumpdata | tail -n +2 | python -m json.tool > $2

