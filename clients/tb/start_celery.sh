#!/bin/bash
celery worker -A atomica_apps.apptasks_tb -l info
