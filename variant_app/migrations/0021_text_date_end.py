# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-19 18:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('variant_app', '0020_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='date_end',
            field=models.DateField(default=None, null=True),
        ),
    ]