#!/bin/sh
set -e

echo "Waiting for Redis..."
until redis-cli -u "$BLOG_REDIS_URL" ping 2>/dev/null | grep -q PONG; do
  sleep 1
done
echo "Redis ready."

if [ "$BLOG_SKIP_DB_SETUP" != "1" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  python manage.py compilemessages || true
  if [ "$BLOG_SEED_DB" = "true" ]; then
    python manage.py seed
  fi
fi

exec "$@"
