# Generated by Django 4.2.5 on 2024-01-20 00:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_alter_gamescore_content_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mathgame',
            name='game_status',
        ),
    ]
