# Generated by Django 5.1.6 on 2025-03-05 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_recipereview'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipereview',
            name='rating',
            field=models.FloatField(),
        ),
    ]
