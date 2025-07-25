# Generated by Django 5.1 on 2025-07-12 14:15

import django.db.models.deletion
import mptt.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('marketplace', '0001_initial'),
        ('shops', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_brands', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='category',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='marketplace.category'),
        ),
        migrations.AddField(
            model_name='brand',
            name='categories',
            field=models.ManyToManyField(related_name='brands', to='marketplace.category'),
        ),
        migrations.AddField(
            model_name='attributevalue',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marketplace.category'),
        ),
        migrations.AddField(
            model_name='product',
            name='attribute_values',
            field=models.ManyToManyField(related_name='product_lines', to='marketplace.attributevalue'),
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='marketplace.brand'),
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='marketplace.category'),
        ),
        migrations.AddField(
            model_name='product',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='product',
            name='shop',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='shops.shop'),
        ),
        migrations.AddField(
            model_name='productimage',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='marketplace.product'),
        ),
        migrations.AddField(
            model_name='whatsappclick',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_clicks', to='marketplace.product'),
        ),
        migrations.AddField(
            model_name='whatsappclick',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='brand',
            index=models.Index(fields=['name'], name='marketplace_name_9ae25c_idx'),
        ),
        migrations.AddIndex(
            model_name='attributevalue',
            index=models.Index(fields=['value'], name='marketplace_value_962af8_idx'),
        ),
        migrations.AddIndex(
            model_name='attributevalue',
            index=models.Index(fields=['category_id'], name='marketplace_categor_189f03_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='attributevalue',
            unique_together={('attribute', 'value', 'category')},
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['brand_id'], name='marketplace_brand_i_cd408b_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category_id'], name='marketplace_categor_0fd450_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['shop_id'], name='marketplace_shop_id_3cdef3_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['owner_id'], name='marketplace_owner_i_8cfc3c_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['created_at'], name='marketplace_created_1f132e_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['location'], name='marketplace_locatio_56048d_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_active', 'location'], name='marketplace_is_acti_6d9aa1_idx'),
        ),
        migrations.AddIndex(
            model_name='whatsappclick',
            index=models.Index(fields=['product', 'clicked_at'], name='marketplace_product_6ee7f3_idx'),
        ),
        migrations.AddIndex(
            model_name='whatsappclick',
            index=models.Index(fields=['clicked_at'], name='marketplace_clicked_b38913_idx'),
        ),
    ]
