# Generated by Django 2.2.24 on 2021-11-30 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stregsystem', '0014_mobilepayment_nullable_customername_20210908_1522'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='caffeine_content_mg',
            field=models.IntegerField(default=0),
        ),
    ]
