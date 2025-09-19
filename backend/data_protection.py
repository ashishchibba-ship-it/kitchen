"""
CRITICAL DATA PROTECTION SYSTEM
This module prevents accidental data loss during development
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class DataProtectionSystem:
    def __init__(self):
        self.mongo_url = os.environ['MONGO_URL']
        self.db_name = os.environ['DB_NAME']
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
    
    async def create_emergency_backup(self, reason="manual_backup"):
        """Create emergency backup of all critical data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_data = {
            "timestamp": timestamp,
            "reason": reason,
            "production_items": [],
            "users": [],
            "orders": [],
            "app_settings": []
        }
        
        try:
            # Backup production items (CRITICAL)
            items = await self.db.production_items.find().to_list(length=None)
            backup_data["production_items"] = items
            
            # Backup users
            users = await self.db.users.find().to_list(length=None)
            backup_data["users"] = users
            
            # Backup orders
            orders = await self.db.orders.find().to_list(length=None)
            backup_data["orders"] = orders
            
            # Backup settings
            settings = await self.db.app_settings.find().to_list(length=None)
            backup_data["app_settings"] = settings
            
            # Save to file
            backup_file = f"/app/emergency_backups/backup_{timestamp}_{reason}.json"
            os.makedirs("/app/emergency_backups", exist_ok=True)
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"✅ Emergency backup created: {backup_file}")
            logger.info(f"📊 Backed up: {len(items)} production items, {len(users)} users, {len(orders)} orders")
            
            return backup_file
            
        except Exception as e:
            logger.error(f"❌ Emergency backup FAILED: {e}")
            raise
    
    async def verify_data_integrity(self):
        """Verify critical data exists"""
        try:
            item_count = await self.db.production_items.count_documents({})
            user_count = await self.db.users.count_documents({})
            
            if item_count == 0:
                logger.warning("⚠️  WARNING: NO PRODUCTION ITEMS FOUND!")
                return False
            
            logger.info(f"✅ Data integrity check: {item_count} items, {user_count} users")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data integrity check FAILED: {e}")
            return False
    
    async def restore_from_backup(self, backup_file):
        """Restore data from emergency backup"""
        logger.info(f"🔄 Restoring from backup: {backup_file}")
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Clear existing data
            await self.db.production_items.delete_many({})
            await self.db.orders.delete_many({})
            await self.db.app_settings.delete_many({})
            
            # Restore production items
            if backup_data["production_items"]:
                await self.db.production_items.insert_many(backup_data["production_items"])
                logger.info(f"✅ Restored {len(backup_data['production_items'])} production items")
            
            # Restore orders
            if backup_data["orders"]:
                await self.db.orders.insert_many(backup_data["orders"])
                logger.info(f"✅ Restored {len(backup_data['orders'])} orders")
            
            # Restore settings
            if backup_data["app_settings"]:
                await self.db.app_settings.insert_many(backup_data["app_settings"])
                logger.info(f"✅ Restored {len(backup_data['app_settings'])} settings")
            
            logger.info("✅ Data restoration completed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data restoration FAILED: {e}")
            return False

# Global instance
protection_system = DataProtectionSystem()

async def auto_backup_before_changes():
    """Automatically backup before any major changes"""
    return await protection_system.create_emergency_backup("auto_before_changes")

async def verify_production_data():
    """Verify production data exists"""
    return await protection_system.verify_data_integrity()