#!/usr/bin/env python3
"""
Script to restore production items exactly as shown in user screenshots
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Production items data extracted from screenshots
PRODUCTION_ITEMS = [
    {"name": "Bao Buns", "category": "Asian Groceries", "unit_of_measure": "carton"},
    {"name": "Beef Patties", "category": "Big Eats", "unit_of_measure": "kilo"},
    {"name": "Chibba's Spiced Chicken", "category": "Appetizers", "unit_of_measure": "kilo"},
    {"name": "Chicken Thigh For Wok", "category": "Big Eats", "unit_of_measure": "kilo"},
    {"name": "Chicken Wings", "category": "Appetizers", "unit_of_measure": "kilo"},
    {"name": "Coconut Powder", "category": "Asian Groceries", "unit_of_measure": "each"},
    {"name": "Crispy Korean Chicken", "category": "Appetizers", "unit_of_measure": "kilo"},
    {"name": "Filipino BBQ Pork", "category": "Skewers", "unit_of_measure": "kilo"},
    {"name": "Japanese Noodles", "category": "Asian Groceries", "unit_of_measure": "each"},
    {"name": "Lamb Kofta", "category": "Skewers", "unit_of_measure": "kilo"},
    {"name": "Marinated Grilled Chicken - Enchiladas", "category": "Appetizers", "unit_of_measure": "kilo"},
    {"name": "Momo Dumplings", "category": "Appetizers", "unit_of_measure": "kilo"},
    {"name": "Peanut Sauce 2kg Tub", "category": "Asian Groceries", "unit_of_measure": "each"},
    {"name": "Pinsa Bread", "category": "Asian Groceries", "unit_of_measure": "each"},
    {"name": "Rice 15kg Bag", "category": "Asian Groceries", "unit_of_measure": "each"},
    {"name": "Rice 1.5kg Bag", "category": "Asian Groceries", "unit_of_measure": "each"},
    {"name": "Roast Pork Belly", "category": "Appetizers", "unit_of_measure": "kilo"},
    {"name": "Satay Chicken", "category": "Skewers", "unit_of_measure": "kilo"},
    {"name": "Slow Cooked Beef Brisket", "category": "Appetizers", "unit_of_measure": "kilo"},
    {"name": "Spicy Citrus Grilled Prawn", "category": "Skewers", "unit_of_measure": "kilo"},
    {"name": "Sriracha Sauce", "category": "Asian Groceries", "unit_of_measure": "each"},
    {"name": "Thai Beef", "category": "Skewers", "unit_of_measure": "kilo"},
    {"name": "Tofu", "category": "Asian Groceries", "unit_of_measure": "kilo"},
]

async def restore_production_items():
    """Clear existing items and restore the original production items"""
    
    print("Starting production items restoration...")
    
    # Clear existing production items
    result = await db.production_items.delete_many({})
    print(f"Deleted {result.deleted_count} existing production items")
    
    # Create new items
    items_to_insert = []
    current_time = datetime.utcnow()
    
    for item_data in PRODUCTION_ITEMS:
        item = {
            "id": str(uuid.uuid4()),
            "name": item_data["name"],
            "category": item_data["category"],
            "unit_of_measure": item_data["unit_of_measure"],
            "assigned_staff": None,
            "image": None,
            "base_cost": 10.0,
            "unit_price": 11.5,  # base_cost * 1.15
            "created_at": current_time,
            "updated_at": current_time
        }
        items_to_insert.append(item)
    
    # Insert all items
    result = await db.production_items.insert_many(items_to_insert)
    print(f"Successfully inserted {len(result.inserted_ids)} production items")
    
    # Print summary
    print("\nRestored items summary:")
    categories = {}
    units = {}
    
    for item in PRODUCTION_ITEMS:
        category = item["category"]
        unit = item["unit_of_measure"]
        
        categories[category] = categories.get(category, 0) + 1
        units[unit] = units.get(unit, 0) + 1
        
        print(f"- {item['name']} ({category}, {unit})")
    
    print(f"\nCategory breakdown:")
    for category, count in categories.items():
        print(f"- {category}: {count} items")
    
    print(f"\nUnit breakdown:")
    for unit, count in units.items():
        print(f"- {unit}: {count} items")
    
    print(f"\nTotal items restored: {len(PRODUCTION_ITEMS)}")

if __name__ == "__main__":
    asyncio.run(restore_production_items())