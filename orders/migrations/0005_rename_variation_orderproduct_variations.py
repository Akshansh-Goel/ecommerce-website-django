# Generated by Django 4.0.1 on 2022-05-21 14:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_remove_orderproduct_variations_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderproduct',
            old_name='variation',
            new_name='variations',
        ),
    ]
