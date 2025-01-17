# Generated by Django 5.1.4 on 2024-12-26 21:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('puzzles', '0013_puzzlefolder_shareall_puzzlefolder_shareonly'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='puzzlefolder',
            name='shareAll',
        ),
        migrations.AddField(
            model_name='config',
            name='default_folder',
            field=models.ForeignKey(help_text='Default Folder to use to share new puzzles.  Leave null to share by making world-editable instead', null=True, on_delete=django.db.models.deletion.CASCADE, to='puzzles.puzzlefolder'),
        ),
        migrations.AddField(
            model_name='config',
            name='default_template',
            field=models.ForeignKey(help_text='Default spreadsheet to use to create new puzzles.  Leave null to create completely blank ones', null=True, on_delete=django.db.models.deletion.CASCADE, to='puzzles.puzzletemplate'),
        ),
        migrations.AlterField(
            model_name='puzzlefolder',
            name='shareOnly',
            field=models.ForeignKey(help_text='User to share this folder with.  Leave null (default) to share with all users', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
