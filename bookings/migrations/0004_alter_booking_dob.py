# Generated by Django 5.2.4 on 2025-07-28 07:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_alter_booking_dob'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='dob',
            field=models.DateField(default=datetime.datetime(2025, 7, 28, 17, 13, 12, 51167)),
        ),
    ]
