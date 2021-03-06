# Generated by Django 4.0.1 on 2022-05-21 14:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_alter_variation_managers'),
        ('orders', '0002_order_phone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderproduct',
            name='variations',
        ),
        migrations.AddField(
            model_name='orderproduct',
            name='variations',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='store.variation'),
            preserve_default=False,
        ),
    ]
