# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-09 02:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('variant_app', '0003_auto_20170108_1739'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='colltoken',
            name='base_token',
        ),
    ]