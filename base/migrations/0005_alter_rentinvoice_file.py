# Generated by Django 5.0 on 2024-09-30 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_rentinvoice_property'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rentinvoice',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='invoices/'),
        ),
    ]
