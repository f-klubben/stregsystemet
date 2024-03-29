# Generated by Django 2.2.24 on 2022-02-11 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stregsystem', '0015_product_caffeine_content_mg'),
    ]

    operations = [
        migrations.CreateModel(
            name='NamedProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='named_id', to='stregsystem.Product')),
            ],
        ),
    ]
