# Generated by Django 3.1.1 on 2020-09-30 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_auto_20200930_2157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='rating',
            field=models.DecimalField(decimal_places=1, default=0, max_digits=2),
        ),
    ]