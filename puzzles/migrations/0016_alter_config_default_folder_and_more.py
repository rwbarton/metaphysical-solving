# Generated by Django 5.1.4 on 2024-12-26 22:43

import django.db.models.deletion
import puzzles.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('puzzles', '0015_puzzle_folder_puzzle_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='config',
            name='default_folder',
            field=models.ForeignKey(blank=True, help_text='Default Folder to use to share new puzzles.  Leave null to share by making world-editable instead', null=True, on_delete=django.db.models.deletion.CASCADE, to='puzzles.puzzlefolder'),
        ),
        migrations.AlterField(
            model_name='config',
            name='default_template',
            field=models.ForeignKey(blank=True, help_text='Default spreadsheet to use to create new puzzles.  Leave null to create completely blank ones', null=True, on_delete=django.db.models.deletion.CASCADE, to='puzzles.puzzletemplate'),
        ),
        migrations.AlterField(
            model_name='puzzle',
            name='folder',
            field=models.ForeignKey(blank=True, default=puzzles.models.defaultFolder, null=True, on_delete=django.db.models.deletion.CASCADE, to='puzzles.puzzlefolder'),
        ),
        migrations.AlterField(
            model_name='puzzle',
            name='template',
            field=models.ForeignKey(blank=True, default=puzzles.models.defaultTemplate, null=True, on_delete=django.db.models.deletion.CASCADE, to='puzzles.puzzletemplate'),
        ),
    ]
