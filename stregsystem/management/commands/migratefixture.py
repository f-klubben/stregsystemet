import tomllib
from django.core.management import BaseCommand, call_command
from pathlib import Path


class Command(BaseCommand):
    help = "Migrate fixtures stored as /**/fixtures/*.json"

    def add_arguments(self, parser):
        parser.add_argument("--fixture", required=True)

    def handle(self, *args, **opts):
        fixture = opts["fixture"]

        targets = self.load_targets()

        self.stdout.write("Migrating to targets")

        for app, migration in targets.items():
            self.stdout.write(f"{app} -> {migration}")
            call_command("migrate", app, migration)

        self.stdout.write("Dumping data")

        with open(fixture, "w") as f:
            call_command(
                "dumpdata",
                exclude=[
                    "auth.permission",
                    "contenttypes",
                    "admin.logentry",
                    "sessions",
                ],
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                stdout=f,
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully migrated fixture')
        )

    def load_targets(self):
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        return data["tool"]["migratefixture"]["targets"]
