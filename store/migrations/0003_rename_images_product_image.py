# Generated by Django 4.0.1 on 2022-02-04 22:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_rename_image_product_images'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='images',
            new_name='image',
        ),
    ]
