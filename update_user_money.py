#!/usr/bin/env python3
"""
Give test user more money for investment testing
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def update_user_money():
    # MongoDB connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Update test user money to 50000 for testing
    result = await db.users.update_one(
        {'email': 'test_jobs@businessempire.com'},
        {'$set': {'money': 50000.0}}
    )
    
    if result.modified_count > 0:
        print("✅ Updated test user money to R$ 50,000.00")
    else:
        print("❌ Failed to update user money")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_user_money())