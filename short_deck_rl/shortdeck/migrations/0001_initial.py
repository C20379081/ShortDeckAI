# Generated by Django 4.2.7 on 2023-11-30 14:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
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
                ("nickname", models.CharField(blank=True, max_length=100)),
                (
                    "avatar",
                    models.CharField(
                        choices=[
                            ("avatar1.png", "Avatar 1"),
                            ("avatar2.png", "Avatar 2"),
                            ("avatar3.png", "Avatar 3"),
                        ],
                        default="avatar1.png",
                        max_length=100,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
