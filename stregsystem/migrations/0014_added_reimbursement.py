from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stregsystem', '0013_mobilepayment_permission_20201123_1344'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='is_reimbursement',
            field=models.BooleanField(default=False, help_text='Viser om en betaling er tilbageført'),
        ),
        migrations.AddField(
            model_name='sale',
            name='is_reimbursed',
            field=models.BooleanField(default=False, help_text='Viser om et salg er tilbageført'),
        ),
    ]
