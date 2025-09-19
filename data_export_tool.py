#!/usr/bin/env python3
"""
EMERGENCY DATA EXPORT TOOL
Run this to backup all your production data including images
"""
import asyncio
import os
import json
import base64
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

load_dotenv('/app/backend/.env')

async def export_all_data():
    """Export all production data to JSON files"""
    
    # Connect to database
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = f"/app/data_exports/export_{timestamp}"
    os.makedirs(export_dir, exist_ok=True)
    
    print(f"🔄 Exporting all data to: {export_dir}")
    
    # Export production items
    items = await db.production_items.find().to_list(length=None)
    with open(f"{export_dir}/production_items.json", 'w') as f:
        json.dump(items, f, indent=2, default=str)
    print(f"✅ Exported {len(items)} production items")
    
    # Export users
    users = await db.users.find().to_list(length=None)
    with open(f"{export_dir}/users.json", 'w') as f:
        json.dump(users, f, indent=2, default=str)
    print(f"✅ Exported {len(users)} users")
    
    # Export orders
    orders = await db.orders.find().to_list(length=None)
    with open(f"{export_dir}/orders.json", 'w') as f:
        json.dump(orders, f, indent=2, default=str)
    print(f"✅ Exported {len(orders)} orders")
    
    # Export settings
    settings = await db.app_settings.find().to_list(length=None)
    with open(f"{export_dir}/app_settings.json", 'w') as f:
        json.dump(settings, f, indent=2, default=str)
    print(f"✅ Exported {len(settings)} app settings")
    
    # Create summary
    summary = {
        "export_timestamp": timestamp,
        "database_name": db_name,
        "production_items_count": len(items),
        "users_count": len(users),
        "orders_count": len(orders),
        "settings_count": len(settings),
        "items_with_images": len([item for item in items if item.get('image')]),
        "total_backup_files": 4
    }
    
    with open(f"{export_dir}/export_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n📊 EXPORT SUMMARY:")
    print(f"Production Items: {summary['production_items_count']}")
    print(f"Items with Images: {summary['items_with_images']}")
    print(f"Users: {summary['users_count']}")
    print(f"Orders: {summary['orders_count']}")
    print(f"Settings: {summary['settings_count']}")
    print(f"\n💾 All data exported to: {export_dir}")
    print("⚠️  SAVE THIS FOLDER - IT'S YOUR COMPLETE BACKUP!")
    
    return export_dir

if __name__ == "__main__":
    asyncio.run(export_all_data())