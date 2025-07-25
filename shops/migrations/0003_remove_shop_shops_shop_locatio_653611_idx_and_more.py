# Generated by Django 5.1 on 2025-07-14 10:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_location_unique_together_and_more'),
        ('shops', '0002_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='shop',
            name='shops_shop_locatio_653611_idx',
        ),
        migrations.RemoveIndex(
            model_name='shop',
            name='shops_shop_is_acti_8e3bfd_idx',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='location',
        ),
        migrations.AddField(
            model_name='shop',
            name='campus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shops', to='core.campus'),
        ),
    ]
