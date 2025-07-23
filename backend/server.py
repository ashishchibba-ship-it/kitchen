from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    MANAGER = "manager"
    KITCHEN_STAFF = "kitchen_staff"
    VENUE_STAFF = "venue_staff"

class ProductionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: UserRole
    username: str

class ProductionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: int
    target_time: str  # Format: "HH:MM"
    production_date: date
    status: ProductionStatus = ProductionStatus.PENDING
    assigned_staff: Optional[str] = None
    cost: Optional[float] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class ProductionItemCreate(BaseModel):
    name: str
    quantity: int
    target_time: str
    production_date: date
    assigned_staff: Optional[str] = None
    cost: Optional[float] = None

class OrderItem(BaseModel):
    production_item_id: str
    production_item_name: str
    quantity: int
    unit_cost: float

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    venue_name: str
    items: List[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    total_cost: float
    markup: float = 15.0  # 15% markup
    final_cost: float
    order_date: datetime = Field(default_factory=datetime.utcnow)
    delivery_date: Optional[datetime] = None

class OrderCreate(BaseModel):
    venue_name: str
    items: List[OrderItem]

# Initialize predefined users
async def init_predefined_users():
    predefined_users = [
        User(name="Kitchen Manager", role=UserRole.MANAGER, username="manager"),
        User(name="Chef Alice", role=UserRole.KITCHEN_STAFF, username="chef_alice"),
        User(name="Chef Bob", role=UserRole.KITCHEN_STAFF, username="chef_bob"),
        User(name="Downtown Cafe", role=UserRole.VENUE_STAFF, username="downtown_cafe"),
        User(name="Uptown Restaurant", role=UserRole.VENUE_STAFF, username="uptown_restaurant"),
    ]
    
    # Check if users already exist
    existing_users = await db.users.count_documents({})
    if existing_users == 0:
        for user in predefined_users:
            await db.users.insert_one(user.dict())

# Authentication endpoints
@api_router.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/users/{username}", response_model=User)
async def get_user_by_username(username: str):
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

# Production management endpoints
@api_router.post("/production-items", response_model=ProductionItem)
async def create_production_item(item: ProductionItemCreate, created_by: str):
    item_dict = item.dict()
    item_dict["created_by"] = created_by
    production_item = ProductionItem(**item_dict)
    
    # Convert date objects to strings for MongoDB storage
    item_data = production_item.dict()
    if isinstance(item_data.get("production_date"), date):
        item_data["production_date"] = item_data["production_date"].isoformat()
    
    await db.production_items.insert_one(item_data)
    return production_item

@api_router.get("/production-items", response_model=List[ProductionItem])
async def get_production_items(production_date: Optional[str] = None, status: Optional[str] = None):
    filter_dict = {}
    if production_date:
        filter_dict["production_date"] = production_date
    if status:
        filter_dict["status"] = status
    
    items = await db.production_items.find(filter_dict).sort("target_time", 1).to_list(1000)
    return [ProductionItem(**item) for item in items]

@api_router.put("/production-items/{item_id}/status")
async def update_production_status(item_id: str, status: ProductionStatus):
    update_data = {"status": status}
    if status == ProductionStatus.COMPLETED:
        update_data["completed_at"] = datetime.utcnow()
    
    result = await db.production_items.update_one(
        {"id": item_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Production item not found")
    
    return {"message": "Status updated successfully"}

@api_router.get("/production-items/completed", response_model=List[ProductionItem])
async def get_completed_items():
    items = await db.production_items.find({"status": "completed"}).to_list(1000)
    return [ProductionItem(**item) for item in items]

# Order management endpoints
@api_router.post("/orders", response_model=Order)
async def create_order(order: OrderCreate):
    # Calculate total cost and final cost with markup
    total_cost = sum(item.quantity * item.unit_cost for item in order.items)
    markup = 15.0
    final_cost = total_cost * (1 + markup / 100)
    
    order_dict = order.dict()
    order_dict["total_cost"] = total_cost
    order_dict["markup"] = markup
    order_dict["final_cost"] = final_cost
    
    new_order = Order(**order_dict)
    await db.orders.insert_one(new_order.dict())
    return new_order

@api_router.get("/orders", response_model=List[Order])
async def get_orders(venue_name: Optional[str] = None):
    filter_dict = {}
    if venue_name:
        filter_dict["venue_name"] = venue_name
    
    orders = await db.orders.find(filter_dict).sort("order_date", -1).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus):
    update_data = {"status": status}
    if status == OrderStatus.DELIVERED:
        update_data["delivery_date"] = datetime.utcnow()
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order status updated successfully"}

# Dashboard endpoints
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    today = date.today().isoformat()
    
    # Production stats
    total_items_today = await db.production_items.count_documents({"production_date": today})
    completed_items_today = await db.production_items.count_documents({
        "production_date": today,
        "status": "completed"
    })
    pending_items_today = await db.production_items.count_documents({
        "production_date": today,
        "status": "pending"
    })
    
    # Order stats
    total_orders_today = await db.orders.count_documents({
        "order_date": {"$gte": datetime.combine(date.today(), datetime.min.time())}
    })
    pending_orders = await db.orders.count_documents({"status": "pending"})
    
    return {
        "production": {
            "total_items_today": total_items_today,
            "completed_items_today": completed_items_today,
            "pending_items_today": pending_items_today,
            "completion_rate": (completed_items_today / total_items_today * 100) if total_items_today > 0 else 0
        },
        "orders": {
            "total_orders_today": total_orders_today,
            "pending_orders": pending_orders
        }
    }

@api_router.get("/")
async def root():
    return {"message": "Production Kitchen Management API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_predefined_users()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()