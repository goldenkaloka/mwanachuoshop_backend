# Generated by Django 5.1 on 2025-07-14 10:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_delete_location'),
        ('estates', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='campus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='properties', to='core.campus'),
        ),
    ]
