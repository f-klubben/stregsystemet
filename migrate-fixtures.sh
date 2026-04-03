set -euo pipefail

for f in stregsystem/fixtures/*.json; do
  python manage.py migratefixture --fixture "$f"
done
