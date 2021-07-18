# Generated by Django 2.2.14 on 2021-07-18 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_order_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='image',
        ),
        migrations.AddField(
            model_name='item',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='static_in_env'),
        ),
    ]
