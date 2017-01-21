from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('variant_app', '0025_query'),
    ]

    operations = [
        TrigramExtension(),
    ]
