#!/usr/bin/env bash
# AutoCon5 WS:C2 — pull every base image used by docker compose, on good wifi.
# Run this AT HOME before Munich. Cached images survive conference-wifi failure.
set -e

echo "Pre-pulling base images for AutoCon5 WS:C2..."
echo "(takes ~3 min on a normal connection, ~200 MB total)"
echo

docker pull redis:7-alpine
docker pull python:3.11-slim

echo
echo "✅ Base images cached. You can now run 'docker compose up' offline."
echo "   First 'up' still builds app images from the cached python:3.11-slim base — ~30 s."
