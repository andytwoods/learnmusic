#!/bin/bash
set -e
gunicorn config.wsgi:application --log-file -
