# Generated by Django 4.1.13 on 2024-09-14 10:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "stregsystem",
            "0018_member_signup_due_paid_alter_mobilepayment_status_and_more",
        ),
        ("stregreport", "0008_auto_20231103_1126"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="RazziaEntry",
            new_name="RazziaEntryOld",
        ),
    ]
