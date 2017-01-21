#!/bin/bash

source variantenv/bin/activate

python manage.py collectstatic
