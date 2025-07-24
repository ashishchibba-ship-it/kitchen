#!/usr/bin/env python3
"""
Backend API Testing for Production Kitchen Management System
Focus: Testing simplified production item creation and category management
Key Changes:
1. Simplified Production Item Creation - no target_time and production_date required
2. Auto-generated defaults - production_date (today) and target_time (12:00)
3. Category Management - CRUD operations
4. Production Items Display - verify items show up correctly
"""

import requests
import json
from datetime import datetime, date, timedelta
import time
import sys

# Backend URL from frontend/.env
BASE_URL = "https://c12dd858-e8b8-4c19-8d91-1deb40e12d63.preview.emergentagent.com/api"

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
            # Test GET /api/production-items (should return all items)
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                all_items = response.json()
                self.log_result("GET /api/production-items", True, f"Retrieved {len(all_items)} total items")
                
                # Verify our created items appear in the list
                created_item_ids = [item["id"] for item in created_items] if created_items else []
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
    
    def run_focused_tests(self):
        """Run focused tests for the updated production kitchen management backend"""
        print("🧪 Starting Focused Backend API Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Focus: Simplified production item creation and category management")
        print("=" * 80)
        
        # Test 1: Simplified Production Item Creation
        created_items = self.test_simplified_production_item_creation()
        
        # Test 2: Category Management CRUD Operations
        self.test_category_management_crud()
        
        # Test 3: Production Items Display
        self.test_production_items_display(created_items)
        
        # Test 4: Categories System Integration
        self.test_categories_system_integration()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 FOCUSED TEST SUMMARY")
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
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)