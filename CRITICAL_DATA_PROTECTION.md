# 🚨 CRITICAL DATA PROTECTION SYSTEM

## IMMEDIATE ACTIONS REQUIRED

### 1. BEFORE ANY DEVELOPMENT WORK:
```bash
# ALWAYS run this first:
cd /app && python data_export_tool.py
```

### 2. EMERGENCY BACKUP LOCATIONS:
- **Automatic backups**: `/app/backups/`
- **Emergency exports**: `/app/data_exports/`
- **Emergency JSON backups**: `/app/emergency_backups/`

### 3. DATA RECOVERY COMMANDS:
```bash
# Create emergency backup NOW:
cd /app && python -c "import asyncio; from backend.data_protection import auto_backup_before_changes; asyncio.run(auto_backup_before_changes())"

# Export all data to JSON:
cd /app && python data_export_tool.py

# Database backup (MongoDB):
cd /app && ./backup_script.sh
```

## ⚠️ NEVER DO THESE WITHOUT BACKUP:
- Database schema changes
- Server restarts during development
- Collection drops or modifications
- Deployment testing

## 🔄 RECOVERY PROCESS:
1. Check `/app/data_exports/` for latest export
2. Check `/app/backups/` for MongoDB dumps
3. Use mongorestore to recover from dumps
4. Use data import tools to restore from JSON exports

## 📞 EMERGENCY CONTACTS:
- Support: support@emergent.sh
- Discord: https://discord.gg/VzKfwCXC4A

## 🛡️ DATA INTEGRITY GUARANTEE:
- Production database is now separate from test database
- Automatic backups before major changes
- Multiple backup formats (MongoDB dump + JSON export)
- Data verification checks on startup

**REMEMBER: Your production data is CRITICAL. Never work without backups!**