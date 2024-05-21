# Generated by Django 4.1.13 on 2024-05-21 15:37

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("stregsystem", "0017_auto_20220511_1738"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="signup_due_paid",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="mobilepayment",
            name="status",
            field=models.CharField(
                choices=[
                    ("U", "Unset"),
                    ("A", "Approved"),
                    ("I", "Ignored"),
                    ("R", "Rejected"),
                ],
                default="U",
                max_length=1,
            ),
        ),
        migrations.CreateModel(
            name="PendingSignup",
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("U", "Unset"),
                            ("A", "Approved"),
                            ("I", "Ignored"),
                            ("R", "Rejected"),
                        ],
                        default="U",
                        max_length=1,
                    ),
                ),
                ("due", models.IntegerField(default=20000)),
                ("token", models.UUIDField(db_index=True, default=uuid.uuid4)),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stregsystem.member",
                    ),
                ),
            ],
            options={
                "permissions": (("signuptool_access", "Sign-up Tool access"),),
            },
        ),
    ]
