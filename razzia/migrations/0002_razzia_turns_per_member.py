# Generated by Django 4.1.13 on 2024-09-14 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("razzia", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="razzia",
            name="turns_per_member",
            field=models.IntegerField(default=0),
        ),
    ]
