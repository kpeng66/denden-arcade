# Generated by Django 4.2.5 on 2023-09-19 23:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0002_remove_room_current_song_remove_room_guest_can_pause_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='users',
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_room', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='members', to='api.room')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
