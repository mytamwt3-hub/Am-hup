#!/bin/bash
# 📊 View Application Logs
# Shows real-time logs from all services

echo ""
echo "📊 Application Logs (Press Ctrl+C to exit)"
echo ""

docker-compose logs -f --tail=50
