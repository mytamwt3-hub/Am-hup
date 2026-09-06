#!/bin/bash
# 🧹 Cleanup Script
# Removes all containers, volumes, and temporary files

echo ""
echo "⚠️  WARNING: This will remove all containers and data!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "🧹 Cleaning up..."
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove Docker images (optional)
    # docker rmi am-hup:latest
    
    # Remove node_modules and package-lock
    rm -rf frontend/node_modules frontend/package-lock.json
    
    # Remove Python cache
    find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find backend -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
    
    # Remove dist folders
    rm -rf frontend/dist
    
    echo ""
    echo "✅ Cleanup complete!"
    echo ""
else
    echo "❌ Cleanup cancelled"
fi
