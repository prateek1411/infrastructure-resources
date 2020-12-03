#!/usr/bin/env bash
# start-server.sh
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 3