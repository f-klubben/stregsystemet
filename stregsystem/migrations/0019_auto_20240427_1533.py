# Generated by Django 2.2.28 on 2024-04-27 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stregsystem', '0018_member_requested_data_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='requested_data_time',
            field=models.DateTimeField(blank=True),
        ),
    ]
