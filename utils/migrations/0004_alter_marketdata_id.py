# Generated by Django 5.0 on 2024-08-17 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0003_alter_marketdata_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketdata',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
