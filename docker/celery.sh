#!/bin/bash

if [[ "${1}" == "celery" ]]; then
  echo "Starting celery worker..."
  celery -A tasks worker --loglevel=info
fi
