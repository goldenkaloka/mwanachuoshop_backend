# Generated by Django 5.1 on 2025-07-12 14:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('payments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='paymentservice',
            index=models.Index(fields=['name'], name='payments_pa_name_e3de94_idx'),
        ),
        migrations.AddField(
            model_name='payment',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='payments.paymentservice'),
        ),
        migrations.AddField(
            model_name='wallet',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='wallettransaction',
            name='payment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wallet_transactions', to='payments.payment'),
        ),
        migrations.AddField(
            model_name='wallettransaction',
            name='wallet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='payments.wallet'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', 'date_added'], name='payments_pa_user_id_0716ad_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['content_type', 'object_id'], name='payments_pa_content_23405f_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_type'], name='payments_pa_payment_09c1c1_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['transaction_id'], name='payments_pa_transac_8e9d99_idx'),
        ),
        migrations.AddIndex(
            model_name='wallet',
            index=models.Index(fields=['user'], name='payments_wa_user_id_cd1a1f_idx'),
        ),
        migrations.AddIndex(
            model_name='wallettransaction',
            index=models.Index(fields=['wallet', 'created_at'], name='payments_wa_wallet__9a8a81_idx'),
        ),
        migrations.AddIndex(
            model_name='wallettransaction',
            index=models.Index(fields=['transaction_type'], name='payments_wa_transac_b6f1b4_idx'),
        ),
        migrations.AddIndex(
            model_name='wallettransaction',
            index=models.Index(fields=['transaction_id'], name='payments_wa_transac_2343f2_idx'),
        ),
    ]
