#!/usr/bin/env bash
# scripts/deploy.sh — run on the Hetzner server
# Usage: ./scripts/deploy.sh
set -euo pipefail

APP_DIR="/opt/taxapp"

log() { echo "[deploy] $*"; }

log "Pulling latest code..."
cd "$APP_DIR"
git pull origin main

log "Building images..."
docker compose build --no-cache

log "Starting services..."
docker compose up -d --remove-orphans

log "Waiting for backend to be healthy..."
timeout 60 bash -c 'until docker compose exec -T backend curl -sf http://localhost:8000/; do sleep 3; done'

log "Running database migrations..."
docker compose exec -T backend alembic upgrade head

log "Cleaning up old images..."
docker image prune -f

log "Deploy complete ✓"
docker compose ps
