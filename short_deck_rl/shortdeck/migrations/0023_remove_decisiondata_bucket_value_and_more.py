# Generated by Django 4.2.7 on 2024-03-02 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shortdeck", "0022_remove_handsplayed_big_blind_user_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="decisiondata",
            name="bucket_value",
        ),
        migrations.AddField(
            model_name="decisiondata",
            name="bucket_values",
            field=models.JSONField(default=None, null=True),
        ),
    ]