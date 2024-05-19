# Generated by Django 4.2.7 on 2024-02-16 20:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("shortdeck", "0008_remove_game_hands_played_handsplayed_game"),
    ]

    operations = [
        migrations.AlterField(
            model_name="handsplayed",
            name="game",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="hands_played",
                to="shortdeck.game",
            ),
        ),
    ]