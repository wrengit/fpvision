# Generated by Django 3.0.8 on 2020-07-07 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_auto_20200707_0801'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='full_slug',
            field=models.CharField(blank=True, max_length=254, unique=True),
        ),
    ]