# Generated by Django 5.1.4 on 2025-01-15 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('puzzles', '0032_queuedhint_response'),
    ]

    operations = [
        migrations.AddField(
            model_name='puzzle',
            name='topic_name',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]