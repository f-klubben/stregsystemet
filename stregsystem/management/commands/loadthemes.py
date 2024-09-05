import json
from os import path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from stregsystem.models import Theme


class Command(BaseCommand):
    help = 'Load themes configuration into the database and/or test fixture'

    def add_arguments(self, parser):
        parser.add_argument(
            "output",
            nargs="?",
            choices=["both", "database", "fixture"],
            default="both",
            help="Choose where to load the themes data",
        )

    def handle(self, *args, **options):

        def load_json(filename):
            with open(filename, 'r') as file:
                return json.load(file)

        def save_json(data, filename):
            with open(filename, 'w') as file:
                json.dump(data, file, indent=2)

        def convert_theme(theme):
            return {
                key: value
                for key, value in {
                    "name": theme.get("name"),
                    "html": theme.get("html"),
                    "css": theme.get("css"),
                    "js": theme.get("js"),
                    "begin_month": theme.get("begin").get("month"),
                    "begin_day": theme.get("begin").get("day"),
                    "end_month": theme.get("end").get("month"),
                    "end_day": theme.get("end").get("day"),
                }.items()
                if value is not None
            }

        # Insert into testdata-themes fixture
        if options["output"] in ["both", "fixture"]:
            model_id = "stregsystem.theme"

            input_themes_path = path.join(settings.BASE_DIR, "stregsystem/themes.json")
            input_testdata_path = path.join(settings.BASE_DIR, "stregsystem/fixtures/testdata.json")
            output_path = path.join(settings.BASE_DIR, "stregsystem/fixtures/testdata-themes.json")

            try:
                themes = load_json(input_themes_path)
                testdata = load_json(input_testdata_path)

                # Remove existing entries of themes just in case there are any
                testdata_filtered = []
                for model in testdata:
                    if model["model"] != model_id:
                        testdata_filtered.append(model)

                # Transform themes into fixture model format
                themes_models = []
                pk = 0
                for theme in themes:
                    pk += 1
                    themes_models.append(
                        {
                            "model": model_id,
                            "pk": pk,
                            "fields": convert_theme(theme),
                        }
                    )

                # Append theme models to testdata
                output = testdata_filtered + themes_models

                save_json(output, output_path)

                self.stdout.write(self.style.SUCCESS('Successfully loaded themes into testdata-themes fixture'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error loading themes into testdata-themes fixture: {str(e)}'))

        # Insert into database
        if options["output"] in ["both", "database"]:
            themes_json_path = path.join(settings.BASE_DIR, "stregsystem/themes.json")
            try:
                themes = load_json(themes_json_path)

                with transaction.atomic():
                    # Delete all existing themes in the database
                    Theme.objects.all().delete()

                    # Add the themes to the database
                    for theme in themes:
                        Theme.objects.create(**convert_theme(theme))

                self.stdout.write(self.style.SUCCESS('Successfully loaded themes into database'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error loading themes into database: {str(e)}'))
