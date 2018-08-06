#!/bin/bash
celery worker -A atomica_apps.apptasks_cascade -l info
