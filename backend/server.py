from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date, timedelta
from enum import Enum
from collections import defaultdict, Counter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io

class ItemAvailability(str, Enum):
    AVAILABLE = "available"
    LIMITED = "limited"
    OUT_OF_STOCK = "out_of_stock"

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

class NotificationPreference(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_role: str
    # Notification types
    order_placed: bool = True
    order_preparing: bool = True  
    order_ready: bool = True
    order_delivered: bool = True
    # Future contact methods
    email: Optional[str] = None
    phone: Optional[str] = None
    # Notification methods (for future use)
    notify_email: bool = True
    notify_sms: bool = False
    notify_in_app: bool = True
    created_at: datetime
    updated_at: datetime

class NotificationEvent(BaseModel):
    id: str
    event_type: str  # 'order_placed', 'order_preparing', 'order_ready', 'order_delivered'
    order_id: str
    message: str
    recipients: List[str]  # user_ids
    created_at: datetime
    read_by: List[str] = []  # user_ids who have read this notification

class ProductionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    unit_of_measure: str = "kg"  # Default to kg
    assigned_staff: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded image
    base_cost: float = 10.0
    unit_price: float = Field(default=0.0)  # Will be calculated as base_cost * 1.15
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProductionItemCreate(BaseModel):
    name: str
    category: str
    unit_of_measure: str = "kg"  # Default to kg
    assigned_staff: Optional[str] = None
    image: Optional[str] = None
    base_cost: float = 10.0

class ProductionItemUpdate(BaseModel):
    available_for_order: Optional[int] = None
    base_cost: Optional[float] = None  # Base cost per unit
    availability_status: Optional[ItemAvailability] = None
    unit_of_measure: Optional[str] = None

class OrderableItem(BaseModel):
    id: str
    name: str
    category: str
    available_quantity: int
    unit_of_measure: str
    unit_price: float
    image: Optional[str] = None
    availability_status: ItemAvailability

class OrderHistory(BaseModel):
    item_id: str
    item_name: str
    category: str
    total_ordered: int
    last_ordered: datetime
    times_ordered: int
    average_quantity: float

class OrderItem(BaseModel):
    production_item_id: str
    production_item_name: str
    quantity: int
    unit_of_measure: str
    unit_price: float = 15.0  # Default price per unit

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    venue_name: str
    venue_id: str
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
    venue_id: str
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

class AppSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    app_name: str = "Production Kitchen Management"
    company_name: str = "Kitchen Co."
    tax_rate: float = 0.08
    default_markup: float = 0.15
    currency: str = "USD"
    timezone: str = "UTC"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AppSettingsUpdate(BaseModel):
    app_name: Optional[str] = None
    company_name: Optional[str] = None
    tax_rate: Optional[float] = None
    default_markup: Optional[float] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None

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

# Notification Management Endpoints
@api_router.get("/notification-preferences", response_model=List[NotificationPreference])
async def get_all_notification_preferences():
    """Get notification preferences for all users"""
    try:
        # Get all users first
        users = await db.users.find({}).to_list(1000)
        preferences = []
        
        for user in users:
            # Check if preferences exist for this user
            existing_pref = await db.notification_preferences.find_one({"user_id": user["id"]})
            
            if existing_pref:
                preferences.append(NotificationPreference(**existing_pref))
            else:
                # Create default preferences for new users
                default_pref = NotificationPreference(
                    id=str(uuid.uuid4()),
                    user_id=user["id"],
                    user_name=user["name"],
                    user_role=user["role"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                await db.notification_preferences.insert_one(default_pref.dict())
                preferences.append(default_pref)
        
        return preferences
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notification preferences: {str(e)}")

@api_router.put("/notification-preferences/{user_id}")
async def update_notification_preferences(user_id: str, preferences: dict):
    """Update notification preferences for a specific user"""
    try:
        # Prepare update data
        update_data = {
            "order_placed": preferences.get("order_placed", True),
            "order_preparing": preferences.get("order_preparing", True),
            "order_ready": preferences.get("order_ready", True),
            "order_delivered": preferences.get("order_delivered", True),
            "email": preferences.get("email"),
            "phone": preferences.get("phone"),
            "notify_email": preferences.get("notify_email", True),
            "notify_sms": preferences.get("notify_sms", False),
            "notify_in_app": preferences.get("notify_in_app", True),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.notification_preferences.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User notification preferences not found")
        
        return {"message": "Notification preferences updated successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating notification preferences: {str(e)}")

@api_router.post("/notifications")
async def create_notification(event_type: str, order_id: str, message: str):
    """Create and send notifications based on event type"""
    try:
        # Get users who should receive this notification
        preferences = await db.notification_preferences.find({
            event_type: True,
            "notify_in_app": True
        }).to_list(1000)
        
        if not preferences:
            return {"message": "No users configured to receive this notification"}
        
        # Create notification event
        notification = NotificationEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            order_id=order_id,
            message=message,
            recipients=[pref["user_id"] for pref in preferences],
            created_at=datetime.utcnow()
        )
        
        await db.notification_events.insert_one(notification.dict())
        
        # In the future, this is where we'll add email/SMS sending logic
        
        return {"message": f"Notification created for {len(preferences)} users", "notification_id": notification.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")

@api_router.get("/notifications/{user_id}")
async def get_user_notifications(user_id: str):
    """Get notifications for a specific user"""
    try:
        notifications = await db.notification_events.find({
            "recipients": user_id
        }).sort("created_at", -1).limit(50).to_list(50)
        
        # Convert to NotificationEvent objects to ensure proper serialization
        serialized_notifications = []
        for notification in notifications:
            try:
                # Convert datetime objects to strings if needed
                if isinstance(notification.get("created_at"), datetime):
                    notification["created_at"] = notification["created_at"].isoformat()
                
                # Ensure all fields are properly serialized
                serialized_notification = {
                    "id": notification.get("id", ""),
                    "event_type": notification.get("event_type", ""),
                    "order_id": notification.get("order_id", ""),
                    "message": notification.get("message", ""),
                    "recipients": notification.get("recipients", []),
                    "created_at": notification.get("created_at", ""),
                    "read_by": notification.get("read_by", [])
                }
                serialized_notifications.append(serialized_notification)
            except Exception as e:
                # Skip invalid notifications
                print(f"Skipping invalid notification: {e}")
                continue
        
        return serialized_notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user_id: str):
    """Mark a notification as read by a user"""
    try:
        result = await db.notification_events.update_one(
            {"id": notification_id},
            {"$addToSet": {"read_by": user_id}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")

# Production management endpoints
@api_router.post("/production-items", response_model=ProductionItem)
async def create_production_item(item: ProductionItemCreate, created_by: str):
    """Create a new production item - immediately available for ordering"""
    try:
        # Create item with auto-generated fields
        item_dict = item.dict()
        item_dict["id"] = str(uuid.uuid4())
        item_dict["created_at"] = datetime.utcnow()
        item_dict["updated_at"] = datetime.utcnow()
        
        # Ensure unit_of_measure defaults to kg
        if not item_dict.get("unit_of_measure"):
            item_dict["unit_of_measure"] = "kg"
        
        # Calculate unit price (15% markup on base_cost)
        base_cost = item_dict.get("base_cost", 10.0)
        item_dict["unit_price"] = base_cost * 1.15
        
        # Insert the item
        await db.production_items.insert_one(item_dict)
        
        return ProductionItem(**item_dict)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating production item: {str(e)}")

@api_router.put("/production-items/{item_id}", response_model=ProductionItem)
async def update_production_item(item_id: str, item_update: ProductionItemCreate):
    """Update a complete production item"""
    update_data = item_update.dict()
    
    # Auto-calculate unit_price with 15% markup
    update_data["unit_price"] = update_data["base_cost"] * 1.15
    
    # Convert date objects to strings for MongoDB storage
    if isinstance(update_data.get("production_date"), date):
        update_data["production_date"] = update_data["production_date"].isoformat()
    
    result = await db.production_items.update_one(
        {"id": item_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Production item not found")
    
    updated_item = await db.production_items.find_one({"id": item_id})
    return ProductionItem(**updated_item)

@api_router.delete("/production-items/{item_id}")
async def delete_production_item(item_id: str, force: bool = False):
    """Delete a production item"""
    try:
        # Check if item exists
        item = await db.production_items.find_one({"id": item_id})
        if not item:
            raise HTTPException(status_code=404, detail="Production item not found")
        
        if not force:
            # Check if item is referenced in any orders (protection mechanism)
            orders_with_item = await db.orders.find({
                "items.production_item_id": item_id
            }).to_list(100)
            
            if orders_with_item:
                order_count = len(orders_with_item)
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete item. It is referenced in {order_count} order(s). Consider updating it instead, or use force delete."
                )
        
        # Delete the item
        result = await db.production_items.delete_one({"id": item_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Production item not found")
        
        if force:
            # If force delete, also remove references from orders
            orders_with_item = await db.orders.find({
                "items.production_item_id": item_id
            }).to_list(100)
            
            for order in orders_with_item:
                # Remove the item from order's items list
                updated_items = [item for item in order.get("items", []) if item.get("production_item_id") != item_id]
                
                # Recalculate order totals
                new_subtotal = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in updated_items)
                new_tax = new_subtotal * 0.08
                new_total = new_subtotal + new_tax
                
                await db.orders.update_one(
                    {"id": order["id"]},
                    {
                        "$set": {
                            "items": updated_items,
                            "subtotal": new_subtotal,
                            "tax_amount": new_tax,
                            "total_amount": new_total
                        }
                    }
                )
            
            # Update related invoices
            invoices_with_item = await db.invoices.find({
                "items.production_item_id": item_id
            }).to_list(100)
            
            for invoice in invoices_with_item:
                # Remove the item from invoice's items list
                updated_items = [item for item in invoice.get("items", []) if item.get("production_item_id") != item_id]
                
                # Recalculate invoice totals
                new_subtotal = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in updated_items)
                new_tax = new_subtotal * 0.08
                new_total = new_subtotal + new_tax
                
                await db.invoices.update_one(
                    {"id": invoice["id"]},
                    {
                        "$set": {
                            "items": updated_items,
                            "subtotal": new_subtotal,
                            "tax_amount": new_tax,
                            "total_amount": new_total
                        }
                    }
                )
        
        return {"message": "Production item deleted successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting production item: {str(e)}")

@api_router.get("/production-items", response_model=List[ProductionItem])
async def get_production_items():
    """Get all production items"""
    items = await db.production_items.find({}).sort("name", 1).to_list(1000)
    
    # Handle backward compatibility for items missing required fields
    valid_items = []
    for item in items:
        try:
            # Ensure required fields exist with defaults
            if "category" not in item:
                item["category"] = "Main Course"
            if "unit_of_measure" not in item:
                item["unit_of_measure"] = "kg"
            if "base_cost" not in item:
                item["base_cost"] = 10.0
            if "unit_price" not in item:
                item["unit_price"] = item.get("base_cost", 10.0) * 1.15
            
            valid_items.append(ProductionItem(**item))
        except Exception as e:
            # Skip invalid items
            print(f"Skipping invalid production item {item.get('id', 'unknown')}: {e}")
            continue
    
    return valid_items

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
    """Get all categories"""
    categories = await db.categories.find().sort("name", 1).to_list(1000)
    category_list = [Category(**cat) for cat in categories]
    return {"categories": [cat.name for cat in category_list]}

@api_router.get("/categories/detailed", response_model=List[Category])
async def get_categories_detailed():
    """Get detailed category information for management"""
    categories = await db.categories.find().sort("name", 1).to_list(1000)
    return [Category(**cat) for cat in categories]

@api_router.post("/categories", response_model=Category)
async def create_category(category: CategoryCreate):
    # Check if category name already exists
    existing_category = await db.categories.find_one({"name": category.name})
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    
    new_category = Category(**category.dict())
    await db.categories.insert_one(new_category.dict())
    return new_category

@api_router.put("/categories/{category_id}", response_model=Category)
async def update_category(category_id: str, category_update: CategoryUpdate):
    # Check if new name is taken (if name is being updated)
    if category_update.name:
        existing_category = await db.categories.find_one({
            "name": category_update.name,
            "id": {"$ne": category_id}
        })
        if existing_category:
            raise HTTPException(status_code=400, detail="Category name already exists")
    
    update_data = {k: v for k, v in category_update.dict().items() if v is not None}
    if update_data:
        result = await db.categories.update_one(
            {"id": category_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Category not found")
    
    updated_category = await db.categories.find_one({"id": category_id})
    return Category(**updated_category)

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    # Check if category is being used by any production items
    items_using_category = await db.production_items.count_documents({"category": category_id})
    if items_using_category > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category that is being used by production items")
    
    result = await db.categories.delete_one({"id": category_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

@api_router.put("/production-items/{item_id}/availability")
async def update_item_availability(item_id: str, update: ProductionItemUpdate):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    
    # If base_cost is being updated, automatically calculate unit_price with 15% markup
    if 'base_cost' in update_data:
        update_data['unit_price'] = update_data['base_cost'] * 1.15
    
    if update_data:
        result = await db.production_items.update_one(
            {"id": item_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Production item not found")
    
    return {"message": "Item availability updated successfully"}

@api_router.get("/orderable-items", response_model=List[OrderableItem])
async def get_orderable_items():
    """Get all items available for ordering (all production items are always available)"""
    items = await db.production_items.find({}).sort("name", 1).to_list(1000)
    
    orderable_items = []
    for item in items:
        # Calculate unit price (15% markup on base_cost)
        unit_price = item.get("base_cost", 10.0) * 1.15
        
        orderable_item = OrderableItem(
            id=item["id"],
            name=item["name"],
            category=item.get("category", "Main Course"),
            available_quantity=1000,  # Always show as available
            unit_of_measure=item.get("unit_of_measure", "kg"),
            unit_price=unit_price,
            image=item.get("image"),
            availability_status="available"
        )
        orderable_items.append(orderable_item)
    
    return orderable_items

@api_router.get("/orderable-items/by-category")
async def get_orderable_items_by_category():
    """Get all items available for ordering organized by category"""
    items = await db.production_items.find({}).sort("name", 1).to_list(1000)
    
    categories = defaultdict(list)
    
    for item in items:
        # Calculate unit price (15% markup on base_cost)
        unit_price = item.get("base_cost", 10.0) * 1.15
        
        category = item.get("category", "Main Course")
        orderable_item = OrderableItem(
            id=item["id"],
            name=item["name"],
            category=category,
            available_quantity=1000,  # Always show as available
            unit_of_measure=item.get("unit_of_measure", "kg"),
            unit_price=unit_price,
            image=item.get("image"),
            availability_status="available"
        )
        categories[category].append(orderable_item)
    
    return dict(categories)

@api_router.get("/order-history/{venue_id}")
async def get_venue_order_history(venue_id: str):
    """Get order history for a venue"""
    orders = await db.orders.find({"venue_id": venue_id}).to_list(1000)
    
    # Aggregate order history
    item_history = defaultdict(lambda: {
        'total_ordered': 0,
        'times_ordered': 0,
        'last_ordered': None,
        'item_name': '',
        'category': ''
    })
    
    for order in orders:
        order_date = order['order_date']
        for item in order['items']:
            item_id = item['production_item_id']
            item_history[item_id]['total_ordered'] += item['quantity']
            item_history[item_id]['times_ordered'] += 1
            item_history[item_id]['item_name'] = item['production_item_name']
            
            if item_history[item_id]['last_ordered'] is None or order_date > item_history[item_id]['last_ordered']:
                item_history[item_id]['last_ordered'] = order_date
    
    # Create OrderHistory objects
    history_list = []
    for item_id, data in item_history.items():
        history_item = OrderHistory(
            item_id=item_id,
            item_name=data['item_name'],
            category=data.get('category', 'Unknown'),
            total_ordered=data['total_ordered'],
            last_ordered=data['last_ordered'],
            times_ordered=data['times_ordered'],
            average_quantity=data['total_ordered'] / data['times_ordered']
        )
        history_list.append(history_item)
    
    # Sort by most frequently ordered
    history_list.sort(key=lambda x: x.times_ordered, reverse=True)
    
    return {
        "most_ordered": history_list[:10],  # Top 10 most ordered
        "recently_ordered": sorted(history_list, key=lambda x: x.last_ordered, reverse=True)[:10]  # Top 10 recently ordered
    }

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
    
    # Create notification for order placed
    await create_notification(
        event_type="order_placed",
        order_id=new_order.id,
        message=f"New order #{invoice_number} from {new_order.venue_name} - ${total_amount:.2f}"
    )
    
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
async def get_orders(venue_name: Optional[str] = None, venue_id: Optional[str] = None, status: Optional[str] = None):
    filter_dict = {}
    if venue_name:
        filter_dict["venue_name"] = venue_name
    if venue_id:
        filter_dict["venue_id"] = venue_id
    if status:
        filter_dict["status"] = status
    
    orders = await db.orders.find(filter_dict).sort("order_date", -1).to_list(1000)
    
    # Handle backward compatibility for old orders
    valid_orders = []
    for order in orders:
        try:
            # Ensure required fields exist with defaults
            if "venue_id" not in order:
                order["venue_id"] = order.get("venue_name", "unknown")
            if "delivery_address" not in order:
                order["delivery_address"] = "Address not specified"
            if "subtotal" not in order:
                order["subtotal"] = 0.0
            if "tax_amount" not in order:
                order["tax_amount"] = 0.0
            if "total_amount" not in order:
                order["total_amount"] = 0.0
            
            # Fix items structure
            if "items" in order:
                for item in order["items"]:
                    if "unit_of_measure" not in item:
                        item["unit_of_measure"] = "units"
            
            # Fix date fields
            if "delivery_date" in order and order["delivery_date"]:
                if isinstance(order["delivery_date"], str):
                    # Already a string, keep as is
                    pass
                else:
                    # Convert datetime to date string
                    order["delivery_date"] = order["delivery_date"].date().isoformat()
            
            valid_orders.append(Order(**order))
        except Exception as e:
            # Skip invalid orders
            print(f"Skipping invalid order {order.get('id', 'unknown')}: {e}")
            continue
    
    return valid_orders

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus):
    """Update order status and trigger notifications"""
    try:
        # Get the order first
        order = await db.orders.find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update the order status
        update_data = {"status": status, "updated_at": datetime.utcnow()}
        if status == OrderStatus.DELIVERED:
            update_data["delivered_at"] = datetime.utcnow()
        
        result = await db.orders.update_one(
            {"id": order_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Create notification based on status change
        status_messages = {
            "preparing": f"Order #{order['invoice_number']} is now being prepared in the kitchen",
            "ready": f"Order #{order['invoice_number']} is ready for pickup/delivery",
            "delivered": f"Order #{order['invoice_number']} has been delivered to {order['venue_name']}"
        }
        
        if status.value in status_messages:
            await create_notification(
                event_type=f"order_{status.value}",
                order_id=order_id,
                message=status_messages[status.value]
            )
        
        return {"message": f"Order status updated to {status.value}"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating order status: {str(e)}")

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

# Helper function for date formatting in PDF
def format_date_for_pdf(date_value):
    """Format date value for PDF display"""
    if not date_value:
        return "N/A"
    
    if isinstance(date_value, str):
        try:
            # Try to parse ISO format string
            parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            return parsed_date.strftime("%Y-%m-%d")
        except:
            return date_value  # Return as-is if parsing fails
    elif isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d")
    elif isinstance(date_value, date):
        return date_value.strftime("%Y-%m-%d")
    else:
        return str(date_value)

@api_router.get("/invoices/{invoice_id}/pdf")
async def export_invoice_pdf(invoice_id: str):
    """Export invoice as PDF for Xero compatibility"""
    try:
        # Get invoice data
        invoice = await db.invoices.find_one({"id": invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("INVOICE", title_style))
        story.append(Spacer(1, 20))
        
        # Invoice details table
        invoice_data = [
            ["Invoice Number:", invoice.get("invoice_number", "N/A")],
            ["Date:", format_date_for_pdf(invoice.get("issue_date"))],
            ["Due Date:", format_date_for_pdf(invoice.get("due_date")) if invoice.get("due_date") else "N/A"],
            ["Customer:", invoice.get("venue_name", "N/A")],
            ["Delivery Address:", invoice.get("delivery_address", "N/A")],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 30))
        
        # Items table
        items_data = [["Item", "Quantity", "Unit", "Unit Price", "Total"]]
        
        for item in invoice.get("items", []):
            item_total = item.get("quantity", 0) * item.get("unit_price", 0)
            items_data.append([
                item.get("production_item_name", "N/A"),
                str(item.get("quantity", 0)),
                item.get("unit_of_measure", "units"),
                f"${item.get('unit_price', 0):.2f}",
                f"${item_total:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals
        subtotal = invoice.get("subtotal", 0)
        tax_amount = invoice.get("tax_amount", 0)
        total_amount = invoice.get("total_amount", 0)
        
        totals_data = [
            ["Subtotal:", f"${subtotal:.2f}"],
            ["Tax (8%):", f"${tax_amount:.2f}"],
            ["Total:", f"${total_amount:.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[4*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
        ]))
        
        story.append(totals_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice_{invoice.get('invoice_number', 'unknown')}.pdf"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

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
    
    # Order stats with new order notifications
    total_orders_today = await db.orders.count_documents({
        "order_date": {"$gte": datetime.combine(date.today(), datetime.min.time())}
    })
    pending_orders = await db.orders.count_documents({"status": "pending"})
    
    # Get recent orders (last 24 hours) for notifications
    recent_orders = await db.orders.find({
        "order_date": {"$gte": datetime.combine(date.today(), datetime.min.time())},
        "status": {"$in": ["pending", "preparing"]}
    }).sort("order_date", -1).limit(10).to_list(10)
    
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
            "daily_revenue": daily_revenue,
            "recent_orders": [
                {
                    "id": order["id"],
                    "venue_name": order["venue_name"],
                    "order_date": order["order_date"],
                    "total_amount": order.get("total_amount", 0),
                    "status": order["status"],
                    "items_count": len(order.get("items", []))
                }
                for order in recent_orders
            ]
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