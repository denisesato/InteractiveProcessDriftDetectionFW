#!/bin/sh
gunicorn index:server -w 2 --threads 2 -b 0.0.0.0:8050