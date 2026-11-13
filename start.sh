#!/bin/bash
set -e
ROLE=${ROLE:-web}
export PYTHONUNBUFFERED=1

if [ "$ROLE" = "web" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput

  PORT=${PORT}
  echo "Starting Gunicorn on port $PORT..."
  exec gunicorn ProjectTemplate.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --access-logfile - \
    --error-logfile - \
    --log-level info
elif [ "$ROLE" = "worker" ]; then
 echo "Starting Celery worker..."
 exec celery -A ProjectTemplate worker --loglevel=info --concurrency=2 --pool=solo
elif [ "$ROLE" = "beat" ]; then
 echo "Starting Celery beat..."
 exec celery -A ProjectTemplate beat --loglevel=info --scheduler=celery.beat.PersistentScheduler --schedule=celerybeat-schedule
else
 echo "❌ Unknown ROLE: $ROLE"
 exit 1
fi