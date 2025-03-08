# Generated by Django 5.1.2 on 2025-03-01 06:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='dietary_tags',
        ),
        migrations.AddField(
            model_name='recipe',
            name='category',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='recipe',
            name='cuisine',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='recipe',
            name='dietary_info',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ingredients',
            field=models.JSONField(),
        ),
    ]
