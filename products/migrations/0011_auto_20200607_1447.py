# Generated by Django 3.0.7 on 2020-06-07 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_auto_20200607_1136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, default='3325533895', max_length=10, unique=True),
        ),
    ]
