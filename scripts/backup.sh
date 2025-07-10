#!/bin/bash

set -e

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
echo "💾 Creating backup in $BACKUP_DIR..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup data directory
if [ -d "data" ]; then
    echo "📄 Backing up documents..."
    cp -r data "$BACKUP_DIR/"
fi

# Backup index directory
if [ -d "index" ]; then
    echo "🔍 Backing up vector index..."
    cp -r index "$BACKUP_DIR/"
fi

# Backup configuration
if [ -f ".env" ]; then
    echo "⚙️  Backing up configuration..."
    cp .env "$BACKUP_DIR/"
fi

# Create backup info
echo "📋 Creating backup info..."
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Backup created: $(date)
Application version: $(grep 'version =' pyproject.toml | cut -d'"' -f2)
Documents count: $(find data -name "*.pdf" 2>/dev/null | wc -l)
Index size: $(du -sh index 2>/dev/null | cut -f1 || echo "N/A")
EOF

echo "✅ Backup completed: $BACKUP_DIR"
echo "📊 Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)" 