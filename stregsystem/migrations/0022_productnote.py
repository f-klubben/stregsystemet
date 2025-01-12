# Generated by Django 4.1.13 on 2025-01-12 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stregsystem", "0021_payment_notes_room_notes"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductNote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
                ("active", models.BooleanField(default=True)),
                (
                    "color",
                    models.CharField(
                        blank="red",
                        help_text="Write a valid html color (default: red)",
                        max_length=20,
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("comment", models.TextField(blank=True)),
                ("products", models.ManyToManyField(to="stregsystem.product")),
                ("rooms", models.ManyToManyField(blank=True, to="stregsystem.room")),
            ],
        ),
    ]
