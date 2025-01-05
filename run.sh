#!/bin/bash
set -e
gunicorn wsgi.py --log-file -
