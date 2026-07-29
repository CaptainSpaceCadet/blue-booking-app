#!/bin/bash
set -e

echo "🚀 Starting Blue Booking App..."
echo "⏳ Waiting for PostgreSQL..."

# More robust PostgreSQL check with timeout
RETRIES=30
until pg_isready -h db -U ${POSTGRES_USER:-blue_booking_user} -d ${POSTGRES_DB:-blue_booking_db} -q || [ $RETRIES -eq 0 ]; do
  echo "PostgreSQL is not ready yet. Waiting... ($RETRIES attempts left)"
  RETRIES=$((RETRIES-1))
  sleep 2
done

if [ $RETRIES -eq 0 ]; then
  echo "⚠️  PostgreSQL is still not ready. Continuing anyway..."
else
  echo "✅ PostgreSQL is ready!"
fi

echo "📦 Running database migrations..."
python manage.py migrate --noinput || echo "⚠️  Migrations failed, but continuing..."

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️  Static files collection failed, but continuing..."

echo "🚀 Starting Uvicorn server..."
exec uvicorn blue_booking_app.asgi:application --host 0.0.0.0 --port 8000 --workers 4