# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-25 02:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('variant_app', '0028_auto_20170122_2123'),
    ]

    operations = [
        migrations.AddField(
            model_name='colltoken',
            name='is_hidden',
            field=models.BooleanField(default=False),
        ),
    ]
