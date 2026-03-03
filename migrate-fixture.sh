### Example usage
# WARNING! Deletes your sqlite database
#
# `sh migrate-fixture.sh refactor/date-attribute stregsystem/fixtures/testdata.json`
# This will load the specified fixture on current `next` branch,
# then it switches to the specified branch, and migrates the database,
# then it dumps the database to the same file.
### 

set -euo pipefail

BRANCH=$1
FIXTURE=$2

# Backup DB
rm -f db.sqlite3.bak
mv db.sqlite3 db.sqlite3.bak

# Load current test data on "next"
git switch next
python manage.py migrate
python manage.py loaddata "$FIXTURE"

# Switch to target branch and migrate
git switch "$BRANCH"
python manage.py migrate

# Dump database WITHOUT framework metadata
python manage.py dumpdata \
  --exclude auth.permission \
  --exclude contenttypes \
  --exclude admin.logentry \
  --exclude sessions \
  --natural-foreign \
  --natural-primary \
  --indent 2 \
  | tail -n +2 \
  > "$FIXTURE"

echo "Fixture updated: $FIXTURE"
