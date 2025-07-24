#!/usr/bin/env python3
"""
Backend API Testing for Production Kitchen Management System
Focus: Testing enhanced visual ordering system features
Key Features to Test:
1. Enhanced Production Items with Ordering Fields (available_for_order, unit_price, availability_status)
2. Manager Item Availability Control (PUT /api/production-items/{id}/availability)
3. Visual Ordering APIs (GET /api/orderable-items, GET /api/orderable-items/by-category)
4. Order History for Personalized Experience (GET /api/order-history/{venue_id})
5. Enhanced Order Management with venue_id and automatic quantity reduction
"""

import requests
import json
from datetime import datetime, date, timedelta
import time
import sys

# Backend URL from frontend/.env
BASE_URL = "https://aeebf561-a946-44b3-821c-29153cfc0885.preview.emergentagent.com/api"

class KitchenAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
    def log_result(self, test_name, success, message=""):
        if success:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED - {message}")
    
    def test_simplified_production_item_creation(self):
        """Test simplified production item creation without target_time and production_date"""
        print("\n=== Testing Simplified Production Item Creation ===")
        
        try:
            # Test creating production items with only required fields
            simplified_items = [
                {
                    "name": "Grilled Chicken Breast",
                    "category": "Main Course",
                    "quantity": 30,
                    "unit_of_measure": "portions",
                    "assigned_staff": "chef_alice"
                },
                {
                    "name": "Fresh Garden Salad",
                    "category": "Salad", 
                    "quantity": 25,
                    "unit_of_measure": "bowls"
                },
                {
                    "name": "Chocolate Chip Cookies",
                    "category": "Dessert",
                    "quantity": 50,
                    "unit_of_measure": "pieces",
                    "assigned_staff": "chef_bob",
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
                }
            ]
            
            created_items = []
            today = date.today().isoformat()
            
            for item_data in simplified_items:
                response = self.session.post(
                    f"{BASE_URL}/production-items?created_by=manager",
                    json=item_data
                )
                
                if response.status_code == 200:
                    item = response.json()
                    created_items.append(item)
                    
                    # Verify auto-generated production_date is today
                    if "production_date" in item and item["production_date"] == today:
                        self.log_result(f"Auto-generated production_date for {item_data['name']}", True, 
                                      f"Date: {item['production_date']}")
                    else:
                        self.log_result(f"Auto-generated production_date for {item_data['name']}", False,
                                      f"Expected {today}, got {item.get('production_date', 'missing')}")
                    
                    # Verify auto-generated target_time is 12:00
                    if "target_time" in item and item["target_time"] == "12:00":
                        self.log_result(f"Auto-generated target_time for {item_data['name']}", True,
                                      f"Time: {item['target_time']}")
                    else:
                        self.log_result(f"Auto-generated target_time for {item_data['name']}", False,
                                      f"Expected 12:00, got {item.get('target_time', 'missing')}")
                    
                    # Verify all provided fields are preserved
                    for field in ["name", "category", "quantity", "unit_of_measure"]:
                        if field in item and item[field] == item_data[field]:
                            self.log_result(f"{field} field for {item_data['name']}", True,
                                          f"{field}: {item[field]}")
                        else:
                            self.log_result(f"{field} field for {item_data['name']}", False,
                                          f"Expected {item_data[field]}, got {item.get(field, 'missing')}")
                    
                    # Verify optional fields
                    if "assigned_staff" in item_data:
                        if item.get("assigned_staff") == item_data["assigned_staff"]:
                            self.log_result(f"assigned_staff for {item_data['name']}", True,
                                          f"Staff: {item['assigned_staff']}")
                        else:
                            self.log_result(f"assigned_staff for {item_data['name']}", False,
                                          f"Expected {item_data['assigned_staff']}, got {item.get('assigned_staff', 'missing')}")
                    
                    if "image" in item_data:
                        if item.get("image") == item_data["image"]:
                            self.log_result(f"image field for {item_data['name']}", True, "Image data preserved")
                        else:
                            self.log_result(f"image field for {item_data['name']}", False, "Image data not preserved")
                    
                    self.log_result(f"Create simplified production item: {item_data['name']}", True,
                                  f"ID: {item['id']}")
                else:
                    self.log_result(f"Create simplified production item: {item_data['name']}", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            return created_items
            
        except Exception as e:
            self.log_result("Simplified Production Item Creation", False, f"Exception: {str(e)}")
            return []
    
    def test_category_management_crud(self):
        """Test comprehensive category CRUD operations"""
        print("\n=== Testing Category Management CRUD Operations ===")
        
        try:
            # Test GET /api/categories (simple format)
            response = self.session.get(f"{BASE_URL}/categories")
            if response.status_code == 200:
                categories_data = response.json()
                if "categories" in categories_data and isinstance(categories_data["categories"], list):
                    categories = categories_data["categories"]
                    self.log_result("GET /api/categories", True, f"Retrieved {len(categories)} category names")
                    
                    # Verify default categories exist
                    expected_defaults = ["Main Course", "Appetizer", "Dessert", "Beverage", "Side Dish", "Salad"]
                    found_defaults = [cat for cat in expected_defaults if cat in categories]
                    
                    if len(found_defaults) >= 4:
                        self.log_result("Default categories present", True, f"Found: {', '.join(found_defaults)}")
                    else:
                        self.log_result("Default categories present", False, f"Only found: {', '.join(found_defaults)}")
                else:
                    self.log_result("GET /api/categories", False, "Invalid response structure")
            else:
                self.log_result("GET /api/categories", False, f"Status: {response.status_code}")
            
            # Test GET /api/categories/detailed (detailed format)
            response = self.session.get(f"{BASE_URL}/categories/detailed")
            if response.status_code == 200:
                detailed_categories = response.json()
                if isinstance(detailed_categories, list) and len(detailed_categories) > 0:
                    self.log_result("GET /api/categories/detailed", True, 
                                  f"Retrieved {len(detailed_categories)} detailed categories")
                    
                    # Verify structure of detailed categories
                    first_cat = detailed_categories[0]
                    required_fields = ["id", "name", "created_at"]
                    if all(field in first_cat for field in required_fields):
                        self.log_result("Detailed category structure", True, "All required fields present")
                    else:
                        missing = [field for field in required_fields if field not in first_cat]
                        self.log_result("Detailed category structure", False, f"Missing fields: {missing}")
                else:
                    self.log_result("GET /api/categories/detailed", False, "Invalid response structure")
            else:
                self.log_result("GET /api/categories/detailed", False, f"Status: {response.status_code}")
            
            # Test POST /api/categories (create new category)
            new_category = {
                "name": "Test Specialty Items",
                "description": "Special test category for API testing"
            }
            
            response = self.session.post(f"{BASE_URL}/categories", json=new_category)
            created_category = None
            if response.status_code == 200:
                created_category = response.json()
                self.log_result("POST /api/categories", True, f"Created category: {created_category['name']}")
                
                # Verify created category structure
                if "id" in created_category and "name" in created_category:
                    self.log_result("Created category structure", True, f"ID: {created_category['id']}")
                else:
                    self.log_result("Created category structure", False, "Missing required fields")
            else:
                self.log_result("POST /api/categories", False, f"Status: {response.status_code}, Response: {response.text}")
            
            # Test PUT /api/categories/{id} (update category)
            if created_category:
                category_id = created_category["id"]
                update_data = {
                    "name": "Updated Test Category",
                    "description": "Updated description for testing"
                }
                
                response = self.session.put(f"{BASE_URL}/categories/{category_id}", json=update_data)
                if response.status_code == 200:
                    updated_category = response.json()
                    if updated_category["name"] == update_data["name"]:
                        self.log_result("PUT /api/categories/{id}", True, f"Updated to: {updated_category['name']}")
                    else:
                        self.log_result("PUT /api/categories/{id}", False, "Name not updated correctly")
                else:
                    self.log_result("PUT /api/categories/{id}", False, f"Status: {response.status_code}")
                
                # Test DELETE /api/categories/{id} (delete category)
                response = self.session.delete(f"{BASE_URL}/categories/{category_id}")
                if response.status_code == 200:
                    self.log_result("DELETE /api/categories/{id}", True, "Category deleted successfully")
                else:
                    self.log_result("DELETE /api/categories/{id}", False, f"Status: {response.status_code}")
            
            # Test duplicate category name prevention
            duplicate_category = {
                "name": "Main Course",  # This should already exist
                "description": "Duplicate test"
            }
            
            response = self.session.post(f"{BASE_URL}/categories", json=duplicate_category)
            if response.status_code == 400:
                self.log_result("Duplicate category prevention", True, "Correctly rejected duplicate name")
            else:
                self.log_result("Duplicate category prevention", False, 
                              f"Expected 400, got {response.status_code}")
            
        except Exception as e:
            self.log_result("Category Management CRUD", False, f"Exception: {str(e)}")
    
    def test_production_items_display(self, created_items):
        """Test that production items display correctly in GET requests"""
        print("\n=== Testing Production Items Display ===")
        
        try:
            created_item_ids = [item["id"] for item in created_items] if created_items else []
            
            # Test GET /api/production-items (should return all items)
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                all_items = response.json()
                self.log_result("GET /api/production-items", True, f"Retrieved {len(all_items)} total items")
                
                # Verify our created items appear in the list
                found_items = [item for item in all_items if item["id"] in created_item_ids]
                
                if len(found_items) == len(created_items):
                    self.log_result("Created items in list", True, f"All {len(created_items)} items found")
                else:
                    self.log_result("Created items in list", False, 
                                  f"Expected {len(created_items)}, found {len(found_items)}")
                
                # Verify items have correct structure and auto-generated fields
                for item in found_items:
                    # Check required fields
                    required_fields = ["id", "name", "category", "quantity", "unit_of_measure", 
                                     "production_date", "target_time", "status", "created_by", "created_at"]
                    missing_fields = [field for field in required_fields if field not in item]
                    
                    if not missing_fields:
                        self.log_result(f"Item structure for {item['name']}", True, "All required fields present")
                    else:
                        self.log_result(f"Item structure for {item['name']}", False, 
                                      f"Missing fields: {missing_fields}")
                    
                    # Verify auto-generated defaults
                    today = date.today().isoformat()
                    if item.get("production_date") == today:
                        self.log_result(f"Production date for {item['name']}", True, f"Date: {item['production_date']}")
                    else:
                        self.log_result(f"Production date for {item['name']}", False, 
                                      f"Expected {today}, got {item.get('production_date')}")
                    
                    if item.get("target_time") == "12:00":
                        self.log_result(f"Target time for {item['name']}", True, f"Time: {item['target_time']}")
                    else:
                        self.log_result(f"Target time for {item['name']}", False, 
                                      f"Expected 12:00, got {item.get('target_time')}")
                
            else:
                self.log_result("GET /api/production-items", False, f"Status: {response.status_code}")
            
            # Test filtering by today's date
            today = date.today().isoformat()
            response = self.session.get(f"{BASE_URL}/production-items?production_date={today}")
            if response.status_code == 200:
                today_items = response.json()
                self.log_result("Filter by today's date", True, f"Retrieved {len(today_items)} items for today")
                
                # All items should be for today since we created them with auto-generated dates
                if created_items:
                    expected_count = len([item for item in today_items if item["id"] in created_item_ids])
                    if expected_count == len(created_items):
                        self.log_result("Today's items filter accuracy", True, 
                                      f"All {len(created_items)} created items found in today's filter")
                    else:
                        self.log_result("Today's items filter accuracy", False,
                                      f"Expected {len(created_items)}, found {expected_count}")
            else:
                self.log_result("Filter by today's date", False, f"Status: {response.status_code}")
            
            # Test filtering by category
            if created_items:
                test_category = created_items[0]["category"]
                response = self.session.get(f"{BASE_URL}/production-items?category={test_category}")
                if response.status_code == 200:
                    category_items = response.json()
                    category_count = len([item for item in category_items if item["category"] == test_category])
                    self.log_result("Filter by category", True, 
                                  f"Retrieved {category_count} items for category '{test_category}'")
                else:
                    self.log_result("Filter by category", False, f"Status: {response.status_code}")
            
            # Test filtering by status (should be 'pending' for new items)
            response = self.session.get(f"{BASE_URL}/production-items?status=pending")
            if response.status_code == 200:
                pending_items = response.json()
                self.log_result("Filter by status", True, f"Retrieved {len(pending_items)} pending items")
                
                # Our created items should be in pending status
                if created_items:
                    pending_created = [item for item in pending_items if item["id"] in created_item_ids]
                    if len(pending_created) == len(created_items):
                        self.log_result("Created items pending status", True, 
                                      f"All {len(created_items)} items have pending status")
                    else:
                        self.log_result("Created items pending status", False,
                                      f"Expected {len(created_items)} pending, found {len(pending_created)}")
            else:
                self.log_result("Filter by status", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Production Items Display", False, f"Exception: {str(e)}")
    
    def test_categories_system_integration(self):
        """Test that the categories system works properly with production items"""
        print("\n=== Testing Categories System Integration ===")
        
        try:
            # Get available categories
            response = self.session.get(f"{BASE_URL}/categories")
            if response.status_code != 200:
                self.log_result("Categories System Integration", False, "Cannot retrieve categories")
                return
            
            categories_data = response.json()
            available_categories = categories_data.get("categories", [])
            
            if not available_categories:
                self.log_result("Categories System Integration", False, "No categories available")
                return
            
            # Test creating production item with each available category
            test_category = available_categories[0] if available_categories else "Main Course"
            
            test_item = {
                "name": "Category Integration Test Item",
                "category": test_category,
                "quantity": 5,
                "unit_of_measure": "units"
            }
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
            if response.status_code == 200:
                created_item = response.json()
                
                # Verify category was set correctly
                if created_item.get("category") == test_category:
                    self.log_result("Category integration with production items", True,
                                  f"Item created with category: {test_category}")
                else:
                    self.log_result("Category integration with production items", False,
                                  f"Expected category {test_category}, got {created_item.get('category')}")
                
                # Test filtering production items by this category
                response = self.session.get(f"{BASE_URL}/production-items?category={test_category}")
                if response.status_code == 200:
                    category_items = response.json()
                    item_found = any(item["id"] == created_item["id"] for item in category_items)
                    
                    if item_found:
                        self.log_result("Category filtering integration", True,
                                      f"Item found when filtering by category {test_category}")
                    else:
                        self.log_result("Category filtering integration", False,
                                      "Item not found in category filter")
                else:
                    self.log_result("Category filtering integration", False, 
                                  f"Category filter failed: {response.status_code}")
            else:
                self.log_result("Category integration with production items", False,
                              f"Failed to create item: {response.status_code}")
                
        except Exception as e:
            self.log_result("Categories System Integration", False, f"Exception: {str(e)}")
    
    def test_enhanced_production_items_with_ordering_fields(self):
        """Test enhanced production items with ordering fields"""
        print("\n=== Testing Enhanced Production Items with Ordering Fields ===")
        
        try:
            # Create production items with enhanced ordering fields
            enhanced_items = [
                {
                    "name": "Premium Grilled Salmon",
                    "category": "Main Course",
                    "quantity": 20,
                    "unit_of_measure": "portions",
                    "assigned_staff": "chef_alice",
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
                },
                {
                    "name": "Artisan Chocolate Cake",
                    "category": "Dessert",
                    "quantity": 15,
                    "unit_of_measure": "slices",
                    "assigned_staff": "chef_bob"
                },
                {
                    "name": "Fresh Caesar Salad",
                    "category": "Salad",
                    "quantity": 25,
                    "unit_of_measure": "bowls"
                }
            ]
            
            created_items = []
            
            for item_data in enhanced_items:
                response = self.session.post(
                    f"{BASE_URL}/production-items?created_by=manager",
                    json=item_data
                )
                
                if response.status_code == 200:
                    item = response.json()
                    created_items.append(item)
                    
                    # Verify enhanced ordering fields exist with defaults
                    ordering_fields = {
                        "available_for_order": 0,
                        "unit_price": 15.0,
                        "availability_status": "available"
                    }
                    
                    for field, expected_default in ordering_fields.items():
                        if field in item:
                            self.log_result(f"Enhanced field {field} for {item_data['name']}", True,
                                          f"{field}: {item[field]}")
                        else:
                            self.log_result(f"Enhanced field {field} for {item_data['name']}", False,
                                          f"Field {field} missing")
                    
                    self.log_result(f"Create enhanced production item: {item_data['name']}", True,
                                  f"ID: {item['id']}")
                else:
                    self.log_result(f"Create enhanced production item: {item_data['name']}", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            return created_items
            
        except Exception as e:
            self.log_result("Enhanced Production Items with Ordering Fields", False, f"Exception: {str(e)}")
            return []

    def test_manager_item_availability_control(self, created_items):
        """Test manager's ability to control item availability for ordering"""
        print("\n=== Testing Manager Item Availability Control ===")
        
        try:
            if not created_items:
                self.log_result("Manager Item Availability Control", False, "No items to test with")
                return []
            
            updated_items = []
            
            for i, item in enumerate(created_items):
                item_id = item["id"]
                item_name = item["name"]
                
                # Set different availability scenarios
                availability_updates = [
                    {
                        "available_for_order": 10,
                        "unit_price": 25.50,
                        "availability_status": "available"
                    },
                    {
                        "available_for_order": 3,
                        "unit_price": 18.75,
                        "availability_status": "limited"
                    },
                    {
                        "available_for_order": 0,
                        "unit_price": 22.00,
                        "availability_status": "out_of_stock"
                    }
                ]
                
                update_data = availability_updates[i % len(availability_updates)]
                
                # Test PUT /api/production-items/{id}/availability
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item_id}/availability",
                    json=update_data
                )
                
                if response.status_code == 200:
                    self.log_result(f"Update availability for {item_name}", True,
                                  f"Available: {update_data['available_for_order']}, Price: ${update_data['unit_price']}")
                    
                    # Verify the update by fetching the item
                    response = self.session.get(f"{BASE_URL}/production-items")
                    if response.status_code == 200:
                        all_items = response.json()
                        updated_item = next((item for item in all_items if item["id"] == item_id), None)
                        
                        if updated_item:
                            # Verify all fields were updated correctly
                            for field, expected_value in update_data.items():
                                actual_value = updated_item.get(field)
                                if actual_value == expected_value:
                                    self.log_result(f"Verify {field} update for {item_name}", True,
                                                  f"{field}: {actual_value}")
                                else:
                                    self.log_result(f"Verify {field} update for {item_name}", False,
                                                  f"Expected {expected_value}, got {actual_value}")
                            
                            updated_items.append(updated_item)
                        else:
                            self.log_result(f"Fetch updated item {item_name}", False, "Item not found after update")
                    else:
                        self.log_result(f"Fetch updated item {item_name}", False, f"Status: {response.status_code}")
                else:
                    self.log_result(f"Update availability for {item_name}", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            return updated_items
            
        except Exception as e:
            self.log_result("Manager Item Availability Control", False, f"Exception: {str(e)}")
            return []

    def test_visual_ordering_apis(self, updated_items):
        """Test visual ordering APIs for the ordering interface"""
        print("\n=== Testing Visual Ordering APIs ===")
        
        try:
            # First, mark some items as completed so they appear in orderable items
            completed_items = []
            for item in updated_items[:2]:  # Mark first 2 items as completed
                item_id = item["id"]
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item_id}/status?status=completed"
                )
                if response.status_code == 200:
                    self.log_result(f"Mark {item['name']} as completed", True, "Status updated to completed")
                    completed_items.append(item)
                else:
                    self.log_result(f"Mark {item['name']} as completed", False, f"Status: {response.status_code}")
            
            # Test GET /api/orderable-items
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                self.log_result("GET /api/orderable-items", True, f"Retrieved {len(orderable_items)} orderable items")
                
                # Verify only completed items with available_for_order > 0 appear
                expected_orderable = [item for item in completed_items if item.get("available_for_order", 0) > 0]
                found_orderable = [item for item in orderable_items if any(comp["id"] == item["id"] for comp in expected_orderable)]
                
                if len(found_orderable) >= len(expected_orderable):
                    self.log_result("Orderable items filtering", True, 
                                  f"Found {len(found_orderable)} items (expected at least {len(expected_orderable)})")
                else:
                    self.log_result("Orderable items filtering", False,
                                  f"Expected at least {len(expected_orderable)}, found {len(found_orderable)}")
                
                # Verify orderable item structure
                if orderable_items:
                    first_item = orderable_items[0]
                    required_fields = ["id", "name", "category", "available_quantity", "unit_of_measure", 
                                     "unit_price", "availability_status"]
                    missing_fields = [field for field in required_fields if field not in first_item]
                    
                    if not missing_fields:
                        self.log_result("Orderable item structure", True, "All required fields present")
                    else:
                        self.log_result("Orderable item structure", False, f"Missing fields: {missing_fields}")
                
            else:
                self.log_result("GET /api/orderable-items", False, f"Status: {response.status_code}")
            
            # Test GET /api/orderable-items/by-category
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                self.log_result("GET /api/orderable-items/by-category", True, 
                              f"Retrieved items organized by {len(items_by_category)} categories")
                
                # Verify structure is a dictionary with categories as keys
                if isinstance(items_by_category, dict):
                    total_items = sum(len(items) for items in items_by_category.values())
                    self.log_result("Category organization structure", True, 
                                  f"Categories: {list(items_by_category.keys())}, Total items: {total_items}")
                    
                    # Verify each category contains proper item structure
                    for category, items in items_by_category.items():
                        if items and isinstance(items, list):
                            first_item = items[0]
                            if "id" in first_item and "name" in first_item and "category" in first_item:
                                self.log_result(f"Category {category} item structure", True, 
                                              f"{len(items)} items with proper structure")
                            else:
                                self.log_result(f"Category {category} item structure", False, 
                                              "Items missing required fields")
                else:
                    self.log_result("Category organization structure", False, "Response is not a dictionary")
            else:
                self.log_result("GET /api/orderable-items/by-category", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Visual Ordering APIs", False, f"Exception: {str(e)}")

    def test_enhanced_order_management_with_venue_id(self, orderable_items_for_order=None):
        """Test enhanced order management with venue_id and automatic quantity reduction"""
        print("\n=== Testing Enhanced Order Management with Venue ID ===")
        
        try:
            # Get venue information first
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code != 200:
                self.log_result("Enhanced Order Management", False, "Cannot retrieve users")
                return []
            
            users = response.json()
            venue_users = [user for user in users if user.get("role") == "venue_staff"]
            
            if not venue_users:
                self.log_result("Enhanced Order Management", False, "No venue users found")
                return []
            
            venue_user = venue_users[0]  # Use first venue user
            venue_id = venue_user["id"]
            venue_name = venue_user["name"]
            venue_address = venue_user.get("address") or "123 Test Street, Test City"
            
            # Get orderable items for the order
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code != 200:
                self.log_result("Enhanced Order Management", False, "Cannot retrieve orderable items")
                return []
            
            orderable_items = response.json()
            if not orderable_items:
                self.log_result("Enhanced Order Management", False, "No orderable items available")
                return []
            
            # Create test orders with venue_id
            test_orders = []
            
            # Order 1: Small order
            order_items_1 = [
                {
                    "production_item_id": orderable_items[0]["id"],
                    "production_item_name": orderable_items[0]["name"],
                    "quantity": 2,
                    "unit_of_measure": orderable_items[0]["unit_of_measure"],
                    "unit_price": orderable_items[0]["unit_price"]
                }
            ]
            
            order_data_1 = {
                "venue_name": venue_name,
                "venue_id": venue_id,
                "delivery_address": venue_address,
                "items": order_items_1,
                "delivery_date": "2024-12-20"
            }
            
            # Store original available quantity for verification
            original_quantity = orderable_items[0]["available_quantity"]
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data_1)
            if response.status_code == 200:
                order_1 = response.json()
                test_orders.append(order_1)
                
                # Verify order structure includes venue_id
                if order_1.get("venue_id") == venue_id:
                    self.log_result("Order with venue_id creation", True, f"Order ID: {order_1['id']}")
                else:
                    self.log_result("Order with venue_id creation", False, 
                                  f"Expected venue_id {venue_id}, got {order_1.get('venue_id')}")
                
                # Verify automatic quantity reduction
                response = self.session.get(f"{BASE_URL}/orderable-items")
                if response.status_code == 200:
                    updated_orderable_items = response.json()
                    updated_item = next((item for item in updated_orderable_items 
                                       if item["id"] == orderable_items[0]["id"]), None)
                    
                    if updated_item:
                        expected_quantity = original_quantity - order_items_1[0]["quantity"]
                        actual_quantity = updated_item["available_quantity"]
                        
                        if actual_quantity == expected_quantity:
                            self.log_result("Automatic quantity reduction", True,
                                          f"Quantity reduced from {original_quantity} to {actual_quantity}")
                        else:
                            self.log_result("Automatic quantity reduction", False,
                                          f"Expected {expected_quantity}, got {actual_quantity}")
                    else:
                        self.log_result("Automatic quantity reduction", False, "Item not found after order")
                else:
                    self.log_result("Automatic quantity reduction", False, "Cannot verify quantity reduction")
                
            else:
                self.log_result("Order with venue_id creation", False,
                              f"Status: {response.status_code}, Response: {response.text}")
            
            # Test GET /api/orders with venue_id filtering
            response = self.session.get(f"{BASE_URL}/orders?venue_id={venue_id}")
            if response.status_code == 200:
                venue_orders = response.json()
                self.log_result("GET /api/orders with venue_id filter", True,
                              f"Retrieved {len(venue_orders)} orders for venue {venue_name}")
                
                # Verify all returned orders belong to the specified venue
                venue_specific = all(order.get("venue_id") == venue_id for order in venue_orders)
                if venue_specific:
                    self.log_result("Venue-specific order filtering", True, "All orders belong to specified venue")
                else:
                    self.log_result("Venue-specific order filtering", False, "Some orders don't belong to specified venue")
            else:
                self.log_result("GET /api/orders with venue_id filter", False, f"Status: {response.status_code}")
            
            return test_orders
            
        except Exception as e:
            self.log_result("Enhanced Order Management with Venue ID", False, f"Exception: {str(e)}")
            return []

    def test_order_history_for_personalized_experience(self, test_orders):
        """Test order history for personalized venue experience"""
        print("\n=== Testing Order History for Personalized Experience ===")
        
        try:
            if not test_orders:
                self.log_result("Order History for Personalized Experience", False, "No test orders available")
                return
            
            # Get venue_id from the first test order
            venue_id = test_orders[0].get("venue_id")
            if not venue_id:
                self.log_result("Order History for Personalized Experience", False, "No venue_id in test orders")
                return
            
            # Create additional orders to build history
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                if len(orderable_items) >= 2:
                    # Create a second order with different items
                    order_items_2 = [
                        {
                            "production_item_id": orderable_items[1]["id"],
                            "production_item_name": orderable_items[1]["name"],
                            "quantity": 3,
                            "unit_of_measure": orderable_items[1]["unit_of_measure"],
                            "unit_price": orderable_items[1]["unit_price"]
                        }
                    ]
                    
                    order_data_2 = {
                        "venue_name": test_orders[0]["venue_name"],
                        "venue_id": venue_id,
                        "delivery_address": test_orders[0]["delivery_address"],
                        "items": order_items_2
                    }
                    
                    response = self.session.post(f"{BASE_URL}/orders", json=order_data_2)
                    if response.status_code == 200:
                        self.log_result("Create additional order for history", True, "Second order created")
                    else:
                        self.log_result("Create additional order for history", False, f"Status: {response.status_code}")
            
            # Test GET /api/order-history/{venue_id}
            response = self.session.get(f"{BASE_URL}/order-history/{venue_id}")
            if response.status_code == 200:
                order_history = response.json()
                self.log_result("GET /api/order-history/{venue_id}", True, "Order history retrieved successfully")
                
                # Verify structure contains most_ordered and recently_ordered
                required_keys = ["most_ordered", "recently_ordered"]
                missing_keys = [key for key in required_keys if key not in order_history]
                
                if not missing_keys:
                    self.log_result("Order history structure", True, "Contains most_ordered and recently_ordered")
                    
                    # Verify most_ordered items
                    most_ordered = order_history["most_ordered"]
                    if isinstance(most_ordered, list):
                        self.log_result("Most ordered items", True, f"Found {len(most_ordered)} most ordered items")
                        
                        # Verify item structure
                        if most_ordered:
                            first_item = most_ordered[0]
                            required_fields = ["item_id", "item_name", "total_ordered", "times_ordered", 
                                             "last_ordered", "average_quantity"]
                            missing_fields = [field for field in required_fields if field not in first_item]
                            
                            if not missing_fields:
                                self.log_result("Most ordered item structure", True, "All required fields present")
                            else:
                                self.log_result("Most ordered item structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("Most ordered items", False, "most_ordered is not a list")
                    
                    # Verify recently_ordered items
                    recently_ordered = order_history["recently_ordered"]
                    if isinstance(recently_ordered, list):
                        self.log_result("Recently ordered items", True, f"Found {len(recently_ordered)} recently ordered items")
                    else:
                        self.log_result("Recently ordered items", False, "recently_ordered is not a list")
                        
                else:
                    self.log_result("Order history structure", False, f"Missing keys: {missing_keys}")
                    
            else:
                self.log_result("GET /api/order-history/{venue_id}", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Order History for Personalized Experience", False, f"Exception: {str(e)}")

    def test_complete_visual_ordering_workflow(self):
        """Test the complete workflow as described in the review request"""
        print("\n=== Testing Complete Visual Ordering Workflow ===")
        
        try:
            # Step 1: Create production items with images and categories
            workflow_items = [
                {
                    "name": "Workflow Test Burger",
                    "category": "Main Course",
                    "quantity": 20,
                    "unit_of_measure": "burgers",
                    "assigned_staff": "chef_alice",
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
                },
                {
                    "name": "Workflow Test Fries",
                    "category": "Side Dish",
                    "quantity": 30,
                    "unit_of_measure": "portions",
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
                }
            ]
            
            created_workflow_items = []
            for item_data in workflow_items:
                response = self.session.post(
                    f"{BASE_URL}/production-items?created_by=manager",
                    json=item_data
                )
                if response.status_code == 200:
                    created_workflow_items.append(response.json())
                    self.log_result(f"Step 1 - Create {item_data['name']} with image and category", True, 
                                  f"Category: {item_data['category']}")
                else:
                    self.log_result(f"Step 1 - Create {item_data['name']}", False, f"Status: {response.status_code}")
            
            # Step 2: Manager sets items available for ordering with specific quantities and prices
            for i, item in enumerate(created_workflow_items):
                availability_data = {
                    "available_for_order": 15 - (i * 5),  # 15, 10
                    "unit_price": 20.0 + (i * 5),  # 20.0, 25.0
                    "availability_status": "available"
                }
                
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item['id']}/availability",
                    json=availability_data
                )
                if response.status_code == 200:
                    self.log_result(f"Step 2 - Set availability for {item['name']}", True,
                                  f"Quantity: {availability_data['available_for_order']}, Price: ${availability_data['unit_price']}")
                else:
                    self.log_result(f"Step 2 - Set availability for {item['name']}", False, f"Status: {response.status_code}")
            
            # Step 3: Mark items as completed so they appear in orderable items
            for item in created_workflow_items:
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item['id']}/status?status=completed"
                )
                if response.status_code == 200:
                    self.log_result(f"Step 3 - Mark {item['name']} as completed", True, "Ready for ordering")
                else:
                    self.log_result(f"Step 3 - Mark {item['name']} as completed", False, f"Status: {response.status_code}")
            
            # Step 4: Test orderable items APIs return proper data with images and categories
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                workflow_orderable = [item for item in orderable_items 
                                    if any(wf_item['id'] == item['id'] for wf_item in created_workflow_items)]
                
                if len(workflow_orderable) == len(created_workflow_items):
                    self.log_result("Step 4 - Orderable items API with images and categories", True,
                                  f"Found {len(workflow_orderable)} items with proper data")
                    
                    # Verify images and categories are present
                    for item in workflow_orderable:
                        if item.get('image') and item.get('category'):
                            self.log_result(f"Step 4 - {item['name']} has image and category", True,
                                          f"Category: {item['category']}")
                        else:
                            self.log_result(f"Step 4 - {item['name']} missing image or category", False,
                                          f"Image: {bool(item.get('image'))}, Category: {item.get('category')}")
                else:
                    self.log_result("Step 4 - Orderable items API", False,
                                  f"Expected {len(created_workflow_items)}, found {len(workflow_orderable)}")
            else:
                self.log_result("Step 4 - Orderable items API", False, f"Status: {response.status_code}")
            
            # Test by-category API
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                categories_found = list(items_by_category.keys())
                expected_categories = ["Main Course", "Side Dish"]
                
                if all(cat in categories_found for cat in expected_categories):
                    self.log_result("Step 4 - Orderable items by category API", True,
                                  f"Categories organized: {categories_found}")
                else:
                    self.log_result("Step 4 - Orderable items by category API", False,
                                  f"Expected {expected_categories}, found {categories_found}")
            else:
                self.log_result("Step 4 - Orderable items by category API", False, f"Status: {response.status_code}")
            
            # Step 5: Place orders and verify quantities automatically reduce
            if workflow_orderable:
                # Get venue info
                response = self.session.get(f"{BASE_URL}/users")
                users = response.json()
                venue_user = next((user for user in users if user.get("role") == "venue_staff"), None)
                
                if venue_user:
                    # Record original quantities
                    original_quantities = {item['id']: item['available_quantity'] for item in workflow_orderable}
                    
                    # Place an order
                    order_items = [
                        {
                            "production_item_id": workflow_orderable[0]["id"],
                            "production_item_name": workflow_orderable[0]["name"],
                            "quantity": 3,
                            "unit_of_measure": workflow_orderable[0]["unit_of_measure"],
                            "unit_price": workflow_orderable[0]["unit_price"]
                        }
                    ]
                    
                    order_data = {
                        "venue_name": venue_user["name"],
                        "venue_id": venue_user["id"],
                        "delivery_address": venue_user.get("address") or "123 Test Street",
                        "items": order_items
                    }
                    
                    response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                    if response.status_code == 200:
                        order = response.json()
                        self.log_result("Step 5 - Place order", True, f"Order ID: {order['id']}")
                        
                        # Verify quantity reduction
                        response = self.session.get(f"{BASE_URL}/orderable-items")
                        if response.status_code == 200:
                            updated_orderable = response.json()
                            updated_item = next((item for item in updated_orderable 
                                               if item['id'] == workflow_orderable[0]['id']), None)
                            
                            if updated_item:
                                original_qty = original_quantities[updated_item['id']]
                                expected_qty = original_qty - 3
                                actual_qty = updated_item['available_quantity']
                                
                                if actual_qty == expected_qty:
                                    self.log_result("Step 5 - Automatic quantity reduction", True,
                                                  f"Reduced from {original_qty} to {actual_qty}")
                                else:
                                    self.log_result("Step 5 - Automatic quantity reduction", False,
                                                  f"Expected {expected_qty}, got {actual_qty}")
                            else:
                                self.log_result("Step 5 - Verify quantity reduction", False, "Item not found")
                        else:
                            self.log_result("Step 5 - Verify quantity reduction", False, "Cannot fetch updated items")
                        
                        # Step 6: Test order history tracking
                        response = self.session.get(f"{BASE_URL}/order-history/{venue_user['id']}")
                        if response.status_code == 200:
                            order_history = response.json()
                            if order_history.get('most_ordered') and order_history.get('recently_ordered'):
                                self.log_result("Step 6 - Order history tracking", True,
                                              f"Most ordered: {len(order_history['most_ordered'])}, Recently ordered: {len(order_history['recently_ordered'])}")
                            else:
                                self.log_result("Step 6 - Order history tracking", False, "Missing history data")
                        else:
                            self.log_result("Step 6 - Order history tracking", False, f"Status: {response.status_code}")
                        
                        # Step 7: Verify venue-specific order filtering
                        response = self.session.get(f"{BASE_URL}/orders?venue_id={venue_user['id']}")
                        if response.status_code == 200:
                            venue_orders = response.json()
                            venue_order_found = any(o['id'] == order['id'] for o in venue_orders)
                            
                            if venue_order_found:
                                self.log_result("Step 7 - Venue-specific order filtering", True,
                                              f"Order found in venue's order list")
                            else:
                                self.log_result("Step 7 - Venue-specific order filtering", False,
                                              "Order not found in venue filter")
                        else:
                            self.log_result("Step 7 - Venue-specific order filtering", False, f"Status: {response.status_code}")
                    else:
                        self.log_result("Step 5 - Place order", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Step 5 - Get venue user", False, "No venue user found")
            else:
                self.log_result("Step 5 - Place order", False, "No orderable items available")
                
        except Exception as e:
            self.log_result("Complete Visual Ordering Workflow", False, f"Exception: {str(e)}")

    def run_visual_ordering_system_tests(self):
        """Run comprehensive tests for the visual ordering system"""
        print("🧪 Starting Visual Ordering System Backend API Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Focus: Enhanced visual ordering system with manager controls and personalized experience")
        print("=" * 80)
        
        # Test 1: Enhanced Production Items with Ordering Fields
        created_items = self.test_enhanced_production_items_with_ordering_fields()
        
        # Test 2: Manager Item Availability Control
        updated_items = self.test_manager_item_availability_control(created_items)
        
        # Test 3: Visual Ordering APIs
        self.test_visual_ordering_apis(updated_items)
        
        # Test 4: Enhanced Order Management with Venue ID
        test_orders = self.test_enhanced_order_management_with_venue_id()
        
        # Test 5: Order History for Personalized Experience
        self.test_order_history_for_personalized_experience(test_orders)
        
        # Test 6: Complete Workflow Test
        self.test_complete_visual_ordering_workflow()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 VISUAL ORDERING SYSTEM TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        if self.test_results['passed'] + self.test_results['failed'] > 0:
            success_rate = (self.test_results['passed'] / 
                           (self.test_results['passed'] + self.test_results['failed']) * 100)
            print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        return self.test_results['failed'] == 0

if __name__ == "__main__":
    tester = KitchenAPITester()
    success = tester.run_visual_ordering_system_tests()
    sys.exit(0 if success else 1)