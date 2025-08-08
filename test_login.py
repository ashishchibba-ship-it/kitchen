#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def test_login():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Test credentials
    username = "updated_manager"
    password = "admin123"
    
    print(f"Testing login for username: {username}")
    print(f"Testing login with password: {password}")
    
    # Find user by username
    user = await db.users.find_one({"username": username})
    if not user:
        print("❌ User not found")
        return
    
    print(f"✅ User found: {user['name']}")
    print(f"✅ Stored password: {user.get('password')}")
    
    # Check password
    if user.get("password") != password:
        print("❌ Password mismatch")
        print(f"Expected: {password}")
        print(f"Got: {user.get('password')}")
        return
    
    print("✅ Password matches!")
    
    # Return user without password
    user_response = {k: v for k, v in user.items() if k != "password"}
    print(f"✅ Login successful for user: {user_response}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_login())