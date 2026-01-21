#!/bin/bash
# Backup script for Neural Memory

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="neural_memory_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "================================"
echo "🗄️  Neural Memory Backup"
echo "================================"

mkdir -p "${BACKUP_PATH}"

# Backup database
echo "Backing up database..."
cp -r ./data "${BACKUP_PATH}/data" 2>/dev/null || echo "No data directory"

# Backup config
echo "Backing up configuration..."
cp docker-compose.yml "${BACKUP_PATH}/" 2>/dev/null
cp .env "${BACKUP_PATH}/.env.backup" 2>/dev/null || echo "No .env file"

# Create metadata
cat > "${BACKUP_PATH}/backup_info.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "backup_name": "${BACKUP_NAME}"
}
EOF

# Calculate size
BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)

echo ""
echo "✅ Backup complete!"
echo "   Location: ${BACKUP_PATH}"
echo "   Size: ${BACKUP_SIZE}"

# Cleanup old backups (keep last 5)
echo ""
echo "Cleaning old backups..."
cd "${BACKUP_DIR}"
ls -dt neural_memory_backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null
echo "✅ Done"
