# Generated by Django 4.2.7 on 2024-02-15 16:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("shortdeck", "0005_gamestatistics_gameaction"),
    ]

    operations = [
        migrations.CreateModel(
            name="HandsPlayed",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("hand_id", models.CharField(max_length=255)),
                ("cards", models.CharField(max_length=255)),
                (
                    "game_actions",
                    models.ManyToManyField(
                        related_name="hands_played", to="shortdeck.gameaction"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="gameaction",
            name="hand",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="shortdeck.handsplayed",
            ),
        ),
    ]