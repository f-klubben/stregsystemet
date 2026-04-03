import tomllib
from django.core.management import BaseCommand, call_command
from django.db import connections
from django.conf import settings
from pathlib import Path
import tempfile
import os


class Command(BaseCommand):
    help = "Migrate fixtures stored as /**/fixtures/*.json"

    def add_arguments(self, parser):
        parser.add_argument("--fixture", required=False)
        parser.add_argument("--update-targets", action="store_true", default=False)

    def handle(self, *args, **opts):
        if opts["update_targets"]:
            self.update_targets()
            return

        if not opts["fixture"]:
            self.stderr.write("Error: --fixture is required, or --update-targets is required")
            return

        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        tmp.close()

        settings.DATABASES["default"]["NAME"] = tmp.name

        try:
            fixture = opts["fixture"]
            targets = self.load_targets()

            self.stdout.write("Migrate all apps to latest")
            call_command("migrate")

            self.stdout.write("Down-migrating to targets in pyproject.toml")
            for app, migration in targets.items():
                self.stdout.write(f"{app} -> {migration}")
                call_command("migrate", app, migration)

            self.stdout.write("Load fixture data")
            call_command("loaddata", fixture)

            self.stdout.write("Re-migrate to targets on pyproject.toml")
            for app, _ in targets.items():
                self.stdout.write(f"{app}")
                call_command("migrate", app)

            self.stdout.write("Dumping fixtures")
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

            self.stdout.write(self.style.SUCCESS('Finished migrating fixtures'))
        finally:
            connections["default"].close()
            os.unlink(tmp.name)

    def load_targets(self):
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        return data["tool"]["migratefixture"]["targets"]

    def update_targets(self):
        from django.db.migrations.loader import MigrationLoader
        from django.db import connection

        loader = MigrationLoader(connection)
        targets = self.load_targets()

        new_targets = {}
        for app in targets:
            leaves = [key for key in loader.graph.leaf_nodes() if key[0] == app]
            if leaves:
                new_targets[app] = leaves[0][1]
                self.stdout.write(f"{app} -> {leaves[0][1]}")

        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        data["tool"]["migratefixture"]["targets"] = new_targets

        import tomli_w
        with open("pyproject.toml", "wb") as f:
            tomli_w.dump(data, f)

        self.stdout.write(self.style.SUCCESS("Updated pyproject.toml targets"))