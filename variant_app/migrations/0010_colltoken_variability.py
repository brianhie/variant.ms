# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-12 22:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('variant_app', '0009_remove_token_coll_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='colltoken',
            name='variability',
            field=models.IntegerField(default=0),
        ),
    ]