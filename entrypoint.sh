#!/bin/bash
set -e

# Setup log directories
mkdir -p /var/log/supervisor
chown -R root:root /var/log/supervisor

# Build DATABASE_URL from individual env vars if not already set
if [ -z "$DATABASE_URL" ]; then
  PG_DB="${POSTGRES_DB:-app}"
  PG_USER="${POSTGRES_USER:-app}"
  PG_PASS="${POSTGRES_PASSWORD:-app}"
  export DATABASE_URL="postgresql://${PG_USER}:${PG_PASS}@localhost:5432/${PG_DB}"
fi

# Ensure PostgreSQL pg_hba.conf allows local connections with md5 auth
PG_HBA="/etc/postgresql/15/main/pg_hba.conf"
if [ -f "$PG_HBA" ]; then
  # Allow password-based connections from localhost
  sed -i 's/^local\s\+all\s\+all\s\+peer/local   all             all                                     md5/' "$PG_HBA"
  # Ensure IPv4 localhost connections use md5
  if ! grep -q "host.*all.*all.*127.0.0.1/32.*md5" "$PG_HBA"; then
    echo "host    all             all             127.0.0.1/32            md5" >> "$PG_HBA"
  fi
fi

echo "Starting Supervisord to launch PostgreSQL, Redis, Django API, and Next.js frontend..."
echo "DATABASE_URL=${DATABASE_URL}"
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
