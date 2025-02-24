# Generated by Django 5.1.6 on 2025-02-24 08:34

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_propertymedia_remove_listing_property_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="phone_number",
            field=models.CharField(
                max_length=13,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must start with +255 or 0, followed by 6 or 7, then 8 digits (e.g., +255712345678 or 0712345678).",
                        regex="^(?:\\+255[6-7]\\d{8}|0[6-7]\\d{8})$",
                    )
                ],
            ),
        ),
    ]
