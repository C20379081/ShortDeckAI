# Generated by Django 4.2.7 on 2024-02-19 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shortdeck", "0011_handsplayed_won_alter_handsplayed_community_cards"),
    ]

    operations = [
        migrations.AddField(
            model_name="handsplayed",
            name="completed",
            field=models.BooleanField(default=False),
        ),
    ]