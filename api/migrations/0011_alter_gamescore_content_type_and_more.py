# Generated by Django 4.2.5 on 2024-01-03 06:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("api", "0010_gamesession_remove_gamescore_game_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gamescore",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AlterField(
            model_name="gamescore",
            name="object_id",
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name="mathgame",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]