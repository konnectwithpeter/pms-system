# Generated by Django 5.0 on 2024-10-05 05:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0010_rename_house_property_unit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tenantprofile',
            old_name='total_monthly_bill',
            new_name='pending_bill',
        ),
    ]
