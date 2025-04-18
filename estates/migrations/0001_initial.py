# Generated by Django 5.2 on 2025-04-16 22:13

import imagekit.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ListingPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('transaction_id', models.CharField(max_length=100, unique=True)),
                ('payment_method', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='ListingPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('listing_type', models.CharField(choices=[('rent', 'For Rent'), ('sale', 'For Sale'), ('shared', 'Shared Space')], max_length=20, unique=True)),
                ('standard_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('featured_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('duration_days', models.PositiveIntegerField(default=30)),
            ],
        ),
        migrations.CreateModel(
            name='PropertyListing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('listing_type', models.CharField(choices=[('rent', 'For Rent'), ('sale', 'For Sale'), ('shared', 'Shared Space')], max_length=20)),
                ('region', models.CharField(max_length=100)),
                ('district', models.CharField(max_length=100)),
                ('street_address', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending Approval'), ('active', 'Active'), ('expired', 'Expired'), ('sold', 'Sold/Rented')], default='draft', max_length=20)),
                ('is_featured', models.BooleanField(default=False)),
                ('featured_expiry', models.DateTimeField(blank=True, null=True)),
                ('virtual_tour', models.URLField(blank=True)),
                ('whatsapp_contact', models.CharField(max_length=15)),
                ('views', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-created_at'],
                'permissions': [('can_verify_listing', 'Can verify property listings')],
            },
        ),
        migrations.CreateModel(
            name='PropertyMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='realestate/')),
                ('media_type', models.CharField(choices=[('image', 'Image'), ('video', 'Video'), ('floorplan', 'Floor Plan')], max_length=20)),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('is_primary', models.BooleanField(default=False)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('thumbnail', imagekit.models.fields.ProcessedImageField(blank=True, upload_to='property_thumbnails/')),
            ],
            options={
                'verbose_name_plural': 'Property media',
                'ordering': ['-is_primary', 'uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='PropertyType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('icon', models.CharField(max_length=30)),
            ],
        ),
    ]
