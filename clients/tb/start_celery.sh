#!/bin/bash
celery worker -A atomica_apps.tb.apptasks -l info
