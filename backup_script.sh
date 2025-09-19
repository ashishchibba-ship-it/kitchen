#!/bin/bash
# Automatic backup script for production database
# Run this before any major changes or testing

BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="production_database"

mkdir -p $BACKUP_DIR

echo "🔒 Creating backup of production database..."
mongodump --db $DB_NAME --out $BACKUP_DIR/backup_$TIMESTAMP

if [ $? -eq 0 ]; then
    echo "✅ Backup completed: $BACKUP_DIR/backup_$TIMESTAMP"
    
    # Keep only last 10 backups to save space
    cd $BACKUP_DIR
    ls -t | tail -n +11 | xargs -d '\n' rm -rf --
    
    echo "📊 Current backups:"
    ls -la $BACKUP_DIR/
else
    echo "❌ Backup failed!"
    exit 1
fi