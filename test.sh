#!/bin/bash

source variantenv/bin/activate

python manage.py test variant_app
