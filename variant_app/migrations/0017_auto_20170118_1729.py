# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-19 01:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('variant_app', '0016_auto_20170118_1726'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corpus',
            name='author',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
