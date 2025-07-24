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
class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: UserRole
    username: str
    address: Optional[str] = None  # For venue staff

class UserCreate(BaseModel):
    name: str
    role: UserRole
    username: str
    address: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    address: Optional[str] = None

class AppSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    primary_color: str = "#3b82f6"
    secondary_color: str = "#1f2937"
    accent_color: str = "#10b981"
    font_family: str = "Inter"
    app_name: str = "Production Kitchen"
    logo_url: Optional[str] = None
    layout_style: str = "modern"  # modern, classic, compact
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AppSettingsUpdate(BaseModel):
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    app_name: Optional[str] = None
    logo_url: Optional[str] = None
    layout_style: Optional[str] = None

class ProductionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    quantity: int
    unit_of_measure: str
    target_time: str  # Format: "HH:MM"
    production_date: date
    status: ProductionStatus = ProductionStatus.PENDING
    assigned_staff: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded image
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class ProductionItemCreate(BaseModel):
    name: str
    category: str
    quantity: int
    unit_of_measure: str
    target_time: str
    production_date: date
    assigned_staff: Optional[str] = None
    image: Optional[str] = None

class OrderItem(BaseModel):
    production_item_id: str
    production_item_name: str
    quantity: int
    unit_of_measure: str
    unit_price: float = 15.0  # Default price per unit

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    venue_name: str
    delivery_address: str
    items: List[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    order_date: datetime = Field(default_factory=datetime.utcnow)
    delivery_date: Optional[date] = None
    delivered_at: Optional[datetime] = None
    subtotal: float
    tax_rate: float = 0.08  # 8% tax
    tax_amount: float
    total_amount: float
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None

class OrderCreate(BaseModel):
    venue_name: str
    delivery_address: str
    items: List[OrderItem]
    delivery_date: Optional[date] = None

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    order_id: str
    venue_name: str
    delivery_address: str
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[date] = None
    items: List[OrderItem]
    subtotal: float
    tax_amount: float
    total_amount: float
    status: str = "pending"  # pending, paid, overdue

class PurchaseOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    po_number: str
    order_id: str
    venue_name: str
    delivery_address: str
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    delivery_date: Optional[date] = None
    items: List[OrderItem]
    subtotal: float
    tax_amount: float
    total_amount: float
    status: str = "pending"  # pending, approved, completed

# Initialize predefined users and settings
async def init_predefined_data():
    # Initialize users
    predefined_users = [
        User(name="Kitchen Manager", role=UserRole.MANAGER, username="manager"),
        User(name="Chef Alice", role=UserRole.KITCHEN_STAFF, username="chef_alice"),
        User(name="Chef Bob", role=UserRole.KITCHEN_STAFF, username="chef_bob"),
        User(name="Downtown Cafe", role=UserRole.VENUE_STAFF, username="downtown_cafe", 
             address="123 Main St, Downtown, City 12345"),
        User(name="Uptown Restaurant", role=UserRole.VENUE_STAFF, username="uptown_restaurant",
             address="456 Oak Ave, Uptown, City 67890"),
    ]
    
    existing_users = await db.users.count_documents({})
    if existing_users == 0:
        for user in predefined_users:
            await db.users.insert_one(user.dict())
    
    # Initialize default app settings
    existing_settings = await db.app_settings.count_documents({})
    if existing_settings == 0:
        default_settings = AppSettings()
        await db.app_settings.insert_one(default_settings.dict())
    
    # Initialize default categories
    existing_categories = await db.categories.count_documents({})
    if existing_categories == 0:
        default_categories = [
            Category(name="Main Course", description="Primary dishes and entrees"),
            Category(name="Appetizer", description="Starters and small plates"),
            Category(name="Dessert", description="Sweet treats and desserts"),
            Category(name="Beverage", description="Drinks and beverages"),
            Category(name="Side Dish", description="Accompaniments and sides"),
            Category(name="Salad", description="Fresh salads and greens"),
        ]
        for category in default_categories:
            await db.categories.insert_one(category.dict())

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

@api_router.post("/users", response_model=User)
async def create_user(user: UserCreate):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_user = User(**user.dict())
    await db.users.insert_one(new_user.dict())
    return new_user

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate):
    # Check if new username is taken (if username is being updated)
    if user_update.username:
        existing_user = await db.users.find_one({
            "username": user_update.username,
            "id": {"$ne": user_id}
        })
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    if update_data:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"id": user_id})
    return User(**updated_user)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# App Settings endpoints
@api_router.get("/settings", response_model=AppSettings)
async def get_app_settings():
    settings = await db.app_settings.find_one()
    if not settings:
        # Create default settings if none exist
        default_settings = AppSettings()
        await db.app_settings.insert_one(default_settings.dict())
        return default_settings
    return AppSettings(**settings)

@api_router.put("/settings", response_model=AppSettings)
async def update_app_settings(settings_update: AppSettingsUpdate):
    update_data = {k: v for k, v in settings_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.app_settings.update_one(
        {},
        {"$set": update_data},
        upsert=True
    )
    
    settings = await db.app_settings.find_one()
    return AppSettings(**settings)

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
async def get_production_items(production_date: Optional[str] = None, status: Optional[str] = None, category: Optional[str] = None):
    filter_dict = {}
    if production_date:
        filter_dict["production_date"] = production_date
    if status:
        filter_dict["status"] = status
    if category:
        filter_dict["category"] = category
    
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

@api_router.get("/categories")
async def get_categories():
    """Get distinct categories from production items"""
    categories = await db.production_items.distinct("category")
    # Add some default categories if none exist
    default_categories = ["Main Course", "Appetizer", "Dessert", "Beverage", "Side Dish", "Salad"]
    all_categories = list(set(categories + default_categories))
    return {"categories": sorted(all_categories)}

# Order management endpoints
@api_router.post("/orders", response_model=Order)
async def create_order(order: OrderCreate):
    # Calculate pricing
    subtotal = sum(item.quantity * item.unit_price for item in order.items)
    tax_rate = 0.08  # 8% tax
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount
    
    # Generate invoice and PO numbers
    order_count = await db.orders.count_documents({}) + 1
    invoice_number = f"INV-{order_count:06d}"
    po_number = f"PO-{order_count:06d}"
    
    order_dict = order.dict()
    order_dict.update({
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "invoice_number": invoice_number,
        "po_number": po_number
    })
    
    new_order = Order(**order_dict)
    
    # Convert date objects to strings for MongoDB storage
    order_data = new_order.dict()
    if isinstance(order_data.get("delivery_date"), date):
        order_data["delivery_date"] = order_data["delivery_date"].isoformat()
    
    await db.orders.insert_one(order_data)
    
    # Auto-generate invoice and purchase order
    await create_invoice_for_order(new_order)
    await create_purchase_order_for_order(new_order)
    
    return new_order

async def create_invoice_for_order(order: Order):
    """Create an invoice for an order"""
    due_date = date.today().replace(day=28) if date.today().day < 28 else (date.today().replace(month=date.today().month + 1, day=28) if date.today().month < 12 else date.today().replace(year=date.today().year + 1, month=1, day=28))
    
    invoice = Invoice(
        invoice_number=order.invoice_number,
        order_id=order.id,
        venue_name=order.venue_name,
        delivery_address=order.delivery_address,
        due_date=due_date,
        items=order.items,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount
    )
    
    invoice_data = invoice.dict()
    if isinstance(invoice_data.get("due_date"), date):
        invoice_data["due_date"] = invoice_data["due_date"].isoformat()
    
    await db.invoices.insert_one(invoice_data)

async def create_purchase_order_for_order(order: Order):
    """Create a purchase order for an order"""
    po = PurchaseOrder(
        po_number=order.po_number,
        order_id=order.id,
        venue_name=order.venue_name,
        delivery_address=order.delivery_address,
        delivery_date=order.delivery_date,
        items=order.items,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount
    )
    
    po_data = po.dict()
    if isinstance(po_data.get("delivery_date"), date):
        po_data["delivery_date"] = po_data["delivery_date"].isoformat()
    
    await db.purchase_orders.insert_one(po_data)

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
        update_data["delivered_at"] = datetime.utcnow()
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order status updated successfully"}

@api_router.put("/orders/{order_id}/delivery-date")
async def update_delivery_date(order_id: str, delivery_date: date):
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": {"delivery_date": delivery_date.isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Delivery date updated successfully"}

# Invoice endpoints
@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices():
    invoices = await db.invoices.find().sort("issue_date", -1).to_list(1000)
    return [Invoice(**invoice) for invoice in invoices]

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return Invoice(**invoice)

@api_router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, status: str):
    result = await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"status": status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {"message": "Invoice status updated successfully"}

# Purchase Order endpoints
@api_router.get("/purchase-orders", response_model=List[PurchaseOrder])
async def get_purchase_orders():
    pos = await db.purchase_orders.find().sort("issue_date", -1).to_list(1000)
    return [PurchaseOrder(**po) for po in pos]

@api_router.get("/purchase-orders/{po_id}", response_model=PurchaseOrder)
async def get_purchase_order(po_id: str):
    po = await db.purchase_orders.find_one({"id": po_id})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return PurchaseOrder(**po)

@api_router.put("/purchase-orders/{po_id}/status")
async def update_purchase_order_status(po_id: str, status: str):
    result = await db.purchase_orders.update_one(
        {"id": po_id},
        {"$set": {"status": status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    return {"message": "Purchase order status updated successfully"}

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
    
    # Financial stats
    today_orders = await db.orders.find({
        "order_date": {"$gte": datetime.combine(date.today(), datetime.min.time())}
    }).to_list(1000)
    daily_revenue = sum(order.get("total_amount", 0) for order in today_orders)
    
    pending_invoices = await db.invoices.count_documents({"status": "pending"})
    
    # Category breakdown
    category_pipeline = [
        {"$match": {"production_date": today}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_stats = await db.production_items.aggregate(category_pipeline).to_list(100)
    
    return {
        "production": {
            "total_items_today": total_items_today,
            "completed_items_today": completed_items_today,
            "pending_items_today": pending_items_today,
            "completion_rate": (completed_items_today / total_items_today * 100) if total_items_today > 0 else 0,
            "categories": {stat["_id"]: stat["count"] for stat in category_stats}
        },
        "orders": {
            "total_orders_today": total_orders_today,
            "pending_orders": pending_orders,
            "daily_revenue": daily_revenue
        },
        "financial": {
            "pending_invoices": pending_invoices,
            "daily_revenue": daily_revenue
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
    await init_predefined_data()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()