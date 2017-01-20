#!/bin/bash

source variantenv/bin/activate

while true
do
    python manage.py runserver 0.0.0.0:80
done
