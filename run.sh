#!/bin/bash

source variantenv/bin/activate

while true
do
    sudo python manage.py runserver 0.0.0.0:80
done
