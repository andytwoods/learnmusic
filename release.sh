#!/bin/bash
set -e
python manage.py migrate
python manage.py setup_app
