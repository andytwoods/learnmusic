#!/bin/bash
set -e
gunicorn project.wsgi --log-file -
