import os
import tempfile
import tomllib
from io import StringIO
from pathlib import Path
from typing import Any

import tomli_w
from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand, CommandParser, call_command
from django.db import connection, connections
from django.db.migrations.loader import MigrationLoader

PYPROJECT_PATH: str = "pyproject.toml"
DUMP_EXCLUDES: list[str] = [
    "auth.permission",
    "contenttypes",
    "admin.logentry",
    "sessions",
]


class Command(BaseCommand):
    help = "Migrate fixtures stored as /**/fixtures/*.json"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--fixture", required=False)
        parser.add_argument("--all-fixtures", action="store_true", default=False)
        parser.add_argument("--app", required=False, help="Limit --all-fixtures to one app label")
        parser.add_argument("--update-targets", action="store_true", default=False)

    def handle(self, *args: Any, **opts: Any) -> None:
        if opts["update_targets"]:
            self._update_targets()
            return

        if not opts["fixture"] and not opts["all_fixtures"]:
            self.stderr.write("Error: --fixture [path], --all-fixtures, or --update-targets is required")
            return

        targets = self._load_targets()

        if opts["all_fixtures"]:
            fixtures = self._find_fixtures(opts["app"])
        else:
            fixtures = [Path(opts["fixture"])]

        for fixture in fixtures:
            self._update_single_fixture(fixture, targets)

        self.stdout.write(self.style.SUCCESS("Finished migrating fixtures"))

    def _find_fixtures(self, app_label: str | None) -> list[Path]:
        project_root = Path.cwd().resolve()
        fixtures: list[Path] = []

        for app_config in apps.get_app_configs():
            if app_label and app_config.label != app_label:
                continue

            app_path = Path(app_config.path).resolve()
            if project_root not in app_path.parents:
                continue  # skip third-party apps

            fixtures_dir = app_path / "fixtures"
            if fixtures_dir.is_dir():
                self.stdout.write(f"Found fixtures in {fixtures_dir}")
                fixtures.extend(sorted(fixtures_dir.glob("*.json")))

        return fixtures

    def _update_single_fixture(self, fixture: Path, targets: dict[str, str]) -> None:
        self.stdout.write(f"Updating {fixture}")
        database_path = self._use_temp_database()

        try:
            self._migrate_to_targets(targets)

            self.stdout.write(f"Load fixture data for {fixture}")
            call_command("loaddata", str(fixture))

            self._migrate_to_latest(targets)
            self._dump_fixture(fixture)

            self.stdout.write(self.style.SUCCESS(f"Finished updating fixture {fixture}"))
        finally:
            connections["default"].close()
            os.unlink(database_path)

    def _use_temp_database(self) -> str:
        connections["default"].close()

        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        tmp.close()

        settings.DATABASES["default"]["NAME"] = tmp.name
        connections["default"].settings_dict["NAME"] = tmp.name

        return tmp.name

    def _migrate_to_targets(self, targets: dict[str, str]) -> None:
        self.stdout.write("Migrate all apps to latest")
        call_command("migrate")

        self.stdout.write("Down-migrating to targets in pyproject.toml")
        for app, migration in targets.items():
            self.stdout.write(f"{app} -> {migration}")
            call_command("migrate", app, migration)

    def _migrate_to_latest(self, targets: dict[str, str]) -> None:
        self.stdout.write("Re-migrate to latest")
        for app in targets:
            self.stdout.write(app)
            call_command("migrate", app)

    def _dump_fixture(self, fixture: Path) -> None:
        self.stdout.write("Dumping fixtures")

        buffer = StringIO()
        call_command(
            "dumpdata",
            exclude=DUMP_EXCLUDES,
            natural_foreign=True,
            natural_primary=True,
            indent=2,
            stdout=buffer,
        )

        # Written only after a successful dump so a failure does not truncate the fixture
        fixture.write_text(buffer.getvalue())

    def _load_targets(self) -> dict[str, str]:
        with open(PYPROJECT_PATH, "rb") as f:
            data = tomllib.load(f)

        return data["tool"]["migratefixture"]["targets"]

    def _update_targets(self) -> None:
        loader = MigrationLoader(connection)
        targets = self._load_targets()

        new_targets: dict[str, str] = {}
        for app in targets:
            leaves = [key for key in loader.graph.leaf_nodes() if key[0] == app]
            if leaves:
                new_targets[app] = leaves[0][1]
                self.stdout.write(f"{app} -> {leaves[0][1]}")

        with open(PYPROJECT_PATH, "rb") as f:
            data = tomllib.load(f)

        data["tool"]["migratefixture"]["targets"] = new_targets

        with open(PYPROJECT_PATH, "wb") as f:
            tomli_w.dump(data, f)

        self.stdout.write(self.style.SUCCESS("Updated pyproject.toml targets"))
