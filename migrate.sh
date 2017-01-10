#!/bin/bash

source variantenv/bin/activate

python manage.py makemigrations
python manage.py migrate
