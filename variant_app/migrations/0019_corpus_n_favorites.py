# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-19 01:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('variant_app', '0018_auto_20170118_1747'),
    ]

    operations = [
        migrations.AddField(
            model_name='corpus',
            name='n_favorites',
            field=models.IntegerField(default=0),
        ),
    ]