# Generated by Django 2.2.24 on 2021-11-24 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stregsystem', '0014_mobilepayment_nullable_customername_20210908_1522'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='caffine_content_ml',
            field=models.FloatField(default=0.0, null=True),
        ),
    ]