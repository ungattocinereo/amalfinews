#!/bin/bash
# View logs from Amalfi Events container

echo "📋 Viewing logs (Ctrl+C to exit)..."
docker-compose logs -f --tail=100
