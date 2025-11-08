#!/bin/bash
# Stop Amalfi Events system

echo "🛑 Stopping Amalfi Events system..."
docker-compose stop

echo "✅ Container stopped"
echo ""
echo "To start again: ./docker-start.sh"
echo "To remove completely: docker-compose down"
