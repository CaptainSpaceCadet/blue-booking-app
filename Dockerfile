FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=blue_booking_app.settings

# Install system dependencies (including PostgreSQL client)
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
COPY package.json package-lock.json ./
RUN npm install && npm install -g webpack webpack-cli

# Copy project files
COPY . .

# Build static files
RUN python manage.py tailwind build && \
    npx webpack --mode=production && \
    python manage.py collectstatic --noinput

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Check database
ENTRYPOINT ["/entrypoint.sh"]

# Run with uvicorn
CMD ["uvicorn", "blue_booking_app.asgi:application", "--host", "0.0.0.0", "--port", "8000"]