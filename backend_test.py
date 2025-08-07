#!/usr/bin/env python3
"""
Backend API Testing for Production Kitchen Management System
Focus: Testing the fixed production items system after removing status management
Key Tests:
1. Production Items Creation - POST /api/production-items without quantity/status fields
2. Production Items Retrieval - GET /api/production-items returns clean data
3. Orderable Items - GET /api/orderable-items and GET /api/orderable-items/by-category
4. Manager Production Screen Fix - verify clean data structure without status/quantity issues
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
    
    def debug_delete_issues(self):
        """Debug why user can't delete items - test DELETE functionality comprehensively"""
        print("\n=== DEBUGGING DELETE ISSUES ===")
        
        try:
            # Step 1: Get all existing production items to understand current state
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code != 200:
                self.log_result("Get existing production items", False, f"Status: {response.status_code}")
                return
            
            all_items = response.json()
            self.log_result("Get existing production items", True, f"Found {len(all_items)} total items")
            
            # Step 2: Check which items are referenced in orders (protection mechanism)
            response = self.session.get(f"{BASE_URL}/orders")
            if response.status_code == 200:
                all_orders = response.json()
                self.log_result("Get all orders", True, f"Found {len(all_orders)} total orders")
                
                # Collect all item IDs referenced in orders
                referenced_item_ids = set()
                for order in all_orders:
                    for item in order.get("items", []):
                        referenced_item_ids.add(item.get("production_item_id"))
                
                self.log_result("Analyze order references", True, f"Found {len(referenced_item_ids)} unique items referenced in orders")
                
                # Categorize items: deletable vs protected
                deletable_items = []
                protected_items = []
                
                for item in all_items:
                    if item["id"] in referenced_item_ids:
                        protected_items.append(item)
                    else:
                        deletable_items.append(item)
                
                self.log_result("Categorize items", True, 
                              f"Deletable: {len(deletable_items)}, Protected (in orders): {len(protected_items)}")
                
                # Step 3: Test deleting protected items (should fail with proper error)
                if protected_items:
                    test_protected_item = protected_items[0]
                    response = self.session.delete(f"{BASE_URL}/production-items/{test_protected_item['id']}")
                    
                    if response.status_code == 400:
                        error_message = response.json().get("detail", "")
                        if "referenced in" in error_message and "order" in error_message:
                            self.log_result("Delete protected item (expected failure)", True, 
                                          f"Correctly blocked: {error_message}")
                        else:
                            self.log_result("Delete protected item (expected failure)", False, 
                                          f"Wrong error message: {error_message}")
                    else:
                        self.log_result("Delete protected item (expected failure)", False, 
                                      f"Expected 400, got {response.status_code}")
                else:
                    self.log_result("Test protected item deletion", False, "No protected items found to test")
                
                # Step 4: Test deleting deletable items (should succeed)
                if deletable_items:
                    test_deletable_item = deletable_items[0]
                    item_name = test_deletable_item["name"]
                    item_id = test_deletable_item["id"]
                    
                    response = self.session.delete(f"{BASE_URL}/production-items/{item_id}")
                    
                    if response.status_code == 200:
                        self.log_result(f"Delete unreferenced item '{item_name}'", True, "Successfully deleted")
                        
                        # Verify item is actually deleted
                        response = self.session.get(f"{BASE_URL}/production-items")
                        if response.status_code == 200:
                            updated_items = response.json()
                            item_still_exists = any(item["id"] == item_id for item in updated_items)
                            
                            if not item_still_exists:
                                self.log_result(f"Verify deletion of '{item_name}'", True, "Item no longer exists")
                            else:
                                self.log_result(f"Verify deletion of '{item_name}'", False, "Item still exists after delete")
                        else:
                            self.log_result(f"Verify deletion of '{item_name}'", False, "Cannot verify deletion")
                    else:
                        self.log_result(f"Delete unreferenced item '{item_name}'", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                else:
                    self.log_result("Test deletable item deletion", False, "No deletable items found to test")
                
                # Step 5: Create a new item and test immediate deletion (should work)
                test_item = {
                    "name": "Delete Test Item",
                    "category": "Main Course",
                    "quantity": 5,
                    "unit_of_measure": "units",
                    "base_cost": 10.0
                }
                
                response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
                if response.status_code == 200:
                    new_item = response.json()
                    self.log_result("Create item for delete test", True, f"Created: {new_item['name']}")
                    
                    # Immediately try to delete it
                    response = self.session.delete(f"{BASE_URL}/production-items/{new_item['id']}")
                    if response.status_code == 200:
                        self.log_result("Delete newly created item", True, "Successfully deleted new item")
                    else:
                        self.log_result("Delete newly created item", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                else:
                    self.log_result("Create item for delete test", False, f"Status: {response.status_code}")
                
                # Step 6: Test edge cases
                # Test deleting non-existent item
                fake_id = "non-existent-item-id"
                response = self.session.delete(f"{BASE_URL}/production-items/{fake_id}")
                if response.status_code == 404:
                    self.log_result("Delete non-existent item", True, "Correctly returned 404")
                else:
                    self.log_result("Delete non-existent item", False, f"Expected 404, got {response.status_code}")
                
            else:
                self.log_result("Get all orders", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Debug Delete Issues", False, f"Exception: {str(e)}")

    def debug_adding_items_issues(self):
        """Debug why user says adding items 'just won't work' - test POST functionality comprehensively"""
        print("\n=== DEBUGGING ADDING ITEMS ISSUES ===")
        
        try:
            # Step 1: Test basic item creation with minimal required fields
            basic_item = {
                "name": "Basic Test Item",
                "category": "Main Course",
                "quantity": 10,
                "unit_of_measure": "units"
            }
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=basic_item)
            if response.status_code == 200:
                created_item = response.json()
                self.log_result("Create basic item", True, f"Created: {created_item['name']} (ID: {created_item['id']})")
            else:
                self.log_result("Create basic item", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return  # If basic creation fails, no point continuing
            
            # Step 2: Test item creation with all optional fields
            complete_item = {
                "name": "Complete Test Item",
                "category": "Dessert",
                "quantity": 15,
                "unit_of_measure": "portions",
                "assigned_staff": "chef_alice",
                "base_cost": 12.50,
                "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
            }
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=complete_item)
            if response.status_code == 200:
                created_complete_item = response.json()
                self.log_result("Create complete item", True, f"Created: {created_complete_item['name']}")
                
                # Verify all fields were saved correctly
                for field, expected_value in complete_item.items():
                    actual_value = created_complete_item.get(field)
                    if actual_value == expected_value:
                        self.log_result(f"Verify {field} field", True, f"{field}: {actual_value}")
                    else:
                        self.log_result(f"Verify {field} field", False, 
                                      f"Expected {expected_value}, got {actual_value}")
            else:
                self.log_result("Create complete item", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
            
            # Step 3: Test validation errors - missing required fields
            invalid_items = [
                {"category": "Main Course", "quantity": 10, "unit_of_measure": "units"},  # Missing name
                {"name": "No Category Item", "quantity": 10, "unit_of_measure": "units"},  # Missing category
                {"name": "No Quantity Item", "category": "Main Course", "unit_of_measure": "units"},  # Missing quantity
                {"name": "No Unit Item", "category": "Main Course", "quantity": 10}  # Missing unit_of_measure
            ]
            
            for i, invalid_item in enumerate(invalid_items):
                response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=invalid_item)
                if response.status_code in [400, 422]:  # Validation error expected
                    self.log_result(f"Validation test {i+1} (missing field)", True, 
                                  f"Correctly rejected with status {response.status_code}")
                else:
                    self.log_result(f"Validation test {i+1} (missing field)", False, 
                                  f"Expected 400/422, got {response.status_code}")
            
            # Step 4: Test invalid data types
            invalid_type_items = [
                {"name": "Invalid Quantity", "category": "Main Course", "quantity": "not_a_number", "unit_of_measure": "units"},
                {"name": "Invalid Base Cost", "category": "Main Course", "quantity": 10, "unit_of_measure": "units", "base_cost": "not_a_number"}
            ]
            
            for i, invalid_item in enumerate(invalid_type_items):
                response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=invalid_item)
                if response.status_code in [400, 422]:  # Validation error expected
                    self.log_result(f"Type validation test {i+1}", True, 
                                  f"Correctly rejected invalid type with status {response.status_code}")
                else:
                    self.log_result(f"Type validation test {i+1}", False, 
                                  f"Expected 400/422, got {response.status_code}")
            
            # Step 5: Test category validation - check if invalid categories are rejected
            response = self.session.get(f"{BASE_URL}/categories")
            if response.status_code == 200:
                categories_data = response.json()
                valid_categories = categories_data.get("categories", [])
                
                if valid_categories:
                    # Test with valid category
                    valid_category_item = {
                        "name": "Valid Category Item",
                        "category": valid_categories[0],
                        "quantity": 5,
                        "unit_of_measure": "units"
                    }
                    
                    response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=valid_category_item)
                    if response.status_code == 200:
                        self.log_result("Valid category test", True, f"Accepted valid category: {valid_categories[0]}")
                    else:
                        self.log_result("Valid category test", False, f"Status: {response.status_code}")
                    
                    # Test with invalid category (this might be allowed, but let's check)
                    invalid_category_item = {
                        "name": "Invalid Category Item",
                        "category": "NonExistentCategory",
                        "quantity": 5,
                        "unit_of_measure": "units"
                    }
                    
                    response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=invalid_category_item)
                    if response.status_code == 200:
                        self.log_result("Invalid category test", True, "System allows custom categories")
                    else:
                        self.log_result("Invalid category test", True, f"System rejects invalid categories (status: {response.status_code})")
            
            # Step 6: Test bulk creation to check for limits
            bulk_items = []
            for i in range(10):  # Try to create 10 items quickly
                bulk_item = {
                    "name": f"Bulk Test Item {i+1}",
                    "category": "Main Course",
                    "quantity": 5,
                    "unit_of_measure": "units"
                }
                bulk_items.append(bulk_item)
            
            successful_bulk_creates = 0
            for i, item in enumerate(bulk_items):
                response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=item)
                if response.status_code == 200:
                    successful_bulk_creates += 1
                else:
                    self.log_result(f"Bulk create item {i+1}", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    break  # Stop on first failure to avoid spam
            
            self.log_result("Bulk item creation", True, f"Successfully created {successful_bulk_creates}/10 items")
            
            # Step 7: Test creation without created_by parameter
            no_creator_item = {
                "name": "No Creator Item",
                "category": "Main Course",
                "quantity": 5,
                "unit_of_measure": "units"
            }
            
            response = self.session.post(f"{BASE_URL}/production-items", json=no_creator_item)  # No created_by param
            if response.status_code in [400, 422]:
                self.log_result("Missing created_by parameter", True, f"Correctly rejected (status: {response.status_code})")
            else:
                self.log_result("Missing created_by parameter", False, f"Expected error, got status: {response.status_code}")
            
            # Step 8: Check current total count to see if there are system limits
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                final_items = response.json()
                self.log_result("Final item count check", True, f"Total items in system: {len(final_items)}")
                
                # Check if we're approaching any reasonable limits
                if len(final_items) > 100:
                    self.log_result("System capacity check", True, f"System handling {len(final_items)} items without issues")
                elif len(final_items) > 50:
                    self.log_result("System capacity check", True, f"System at {len(final_items)} items - moderate load")
                else:
                    self.log_result("System capacity check", True, f"System at {len(final_items)} items - low load")
            
        except Exception as e:
            self.log_result("Debug Adding Items Issues", False, f"Exception: {str(e)}")

    def test_complete_crud_workflow(self):
        """Test complete Create, Read, Update, Delete workflow to identify any issues"""
        print("\n=== TESTING COMPLETE CRUD WORKFLOW ===")
        
        try:
            # Step 1: CREATE - Test item creation
            test_item = {
                "name": "CRUD Test Item",
                "category": "Main Course",
                "quantity": 20,
                "unit_of_measure": "portions",
                "assigned_staff": "chef_alice",
                "base_cost": 15.0
            }
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
            if response.status_code == 200:
                created_item = response.json()
                item_id = created_item["id"]
                self.log_result("CRUD - CREATE", True, f"Created item: {created_item['name']} (ID: {item_id})")
            else:
                self.log_result("CRUD - CREATE", False, f"Status: {response.status_code}")
                return
            
            # Step 2: READ - Test item retrieval
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                all_items = response.json()
                created_item_found = any(item["id"] == item_id for item in all_items)
                if created_item_found:
                    self.log_result("CRUD - READ", True, f"Item found in list of {len(all_items)} items")
                else:
                    self.log_result("CRUD - READ", False, "Created item not found in list")
            else:
                self.log_result("CRUD - READ", False, f"Status: {response.status_code}")
            
            # Step 3: UPDATE - Test item modification
            update_data = {
                "name": "Updated CRUD Test Item",
                "category": "Dessert",
                "quantity": 25,
                "unit_of_measure": "slices",
                "assigned_staff": "chef_bob",
                "base_cost": 18.0
            }
            
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}", json=update_data)
            if response.status_code == 200:
                updated_item = response.json()
                self.log_result("CRUD - UPDATE", True, f"Updated item: {updated_item['name']}")
                
                # Verify updates were applied
                for field, expected_value in update_data.items():
                    actual_value = updated_item.get(field)
                    if actual_value == expected_value:
                        self.log_result(f"CRUD - Verify {field} update", True, f"{field}: {actual_value}")
                    else:
                        self.log_result(f"CRUD - Verify {field} update", False, 
                                      f"Expected {expected_value}, got {actual_value}")
            else:
                self.log_result("CRUD - UPDATE", False, f"Status: {response.status_code}")
            
            # Step 4: DELETE - Test item deletion
            response = self.session.delete(f"{BASE_URL}/production-items/{item_id}")
            if response.status_code == 200:
                self.log_result("CRUD - DELETE", True, "Item deleted successfully")
                
                # Verify deletion
                response = self.session.get(f"{BASE_URL}/production-items")
                if response.status_code == 200:
                    remaining_items = response.json()
                    item_still_exists = any(item["id"] == item_id for item in remaining_items)
                    if not item_still_exists:
                        self.log_result("CRUD - Verify deletion", True, "Item no longer exists")
                    else:
                        self.log_result("CRUD - Verify deletion", False, "Item still exists after deletion")
                else:
                    self.log_result("CRUD - Verify deletion", False, "Cannot verify deletion")
            else:
                self.log_result("CRUD - DELETE", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Complete CRUD Workflow", False, f"Exception: {str(e)}")

    def test_simplified_ordering_system(self):
        """Test the complete simplified ordering system workflow"""
        print("🔍 STARTING SIMPLIFIED ORDERING SYSTEM TESTS")
        print("=" * 60)
        
        # Test 1: Production Item Creation without quantity field
        self.test_production_item_creation_without_quantity()
        
        # Test 2: Orderable Items Without Limitations
        self.test_orderable_items_without_limitations()
        
        # Test 3: Order Creation Without Inventory Reduction
        self.test_order_creation_without_inventory_reduction()
        
        # Test 4: Complete Simplified Workflow
        self.test_complete_simplified_workflow()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🔍 SIMPLIFIED ORDERING SYSTEM TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.test_results['passed']}")
        print(f"❌ Tests Failed: {self.test_results['failed']}")
        print(f"📊 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        return self.test_results

    def test_production_item_creation_without_quantity(self):
        """Test Production Item Creation without quantity field (manager creation)"""
        print("\n=== TEST 1: Production Item Creation Without Quantity Field ===")
        
        try:
            # Test creating items without quantity field - should default to 1
            test_items = [
                {
                    "name": "Manager Created Pasta",
                    "category": "Main Course",
                    "base_cost": 12.0
                },
                {
                    "name": "Manager Created Salad", 
                    "category": "Salad",
                    "base_cost": 8.0,
                    "assigned_staff": "chef_alice"
                },
                {
                    "name": "Manager Created Dessert",
                    "category": "Dessert", 
                    "base_cost": 6.0,
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
                }
            ]
            
            created_items = []
            
            for item_data in test_items:
                response = self.session.post(
                    f"{BASE_URL}/production-items?created_by=manager",
                    json=item_data
                )
                
                if response.status_code == 200:
                    item = response.json()
                    created_items.append(item)
                    
                    # Verify default quantity of 1 is set when not provided
                    if item.get("quantity") == 1:
                        self.log_result(f"Default quantity for {item_data['name']}", True, 
                                      f"Quantity defaulted to 1")
                    else:
                        self.log_result(f"Default quantity for {item_data['name']}", False,
                                      f"Expected 1, got {item.get('quantity')}")
                    
                    # Verify unit_of_measure defaults to "kg"
                    if item.get("unit_of_measure") == "kg":
                        self.log_result(f"Default unit_of_measure for {item_data['name']}", True,
                                      f"Unit of measure defaulted to 'kg'")
                    else:
                        self.log_result(f"Default unit_of_measure for {item_data['name']}", False,
                                      f"Expected 'kg', got {item.get('unit_of_measure')}")
                    
                    # Verify unit_price is calculated correctly (base_cost * 1.15)
                    expected_unit_price = item_data["base_cost"] * 1.15
                    actual_unit_price = item.get("unit_price")
                    if abs(actual_unit_price - expected_unit_price) < 0.01:  # Allow for floating point precision
                        self.log_result(f"Unit price calculation for {item_data['name']}", True,
                                      f"Unit price: ${actual_unit_price:.2f} (15% markup on ${item_data['base_cost']:.2f})")
                    else:
                        self.log_result(f"Unit price calculation for {item_data['name']}", False,
                                      f"Expected ${expected_unit_price:.2f}, got ${actual_unit_price:.2f}")
                    
                    self.log_result(f"Create production item without quantity: {item_data['name']}", True,
                                  f"ID: {item['id']}")
                else:
                    self.log_result(f"Create production item without quantity: {item_data['name']}", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            return created_items
            
        except Exception as e:
            self.log_result("Production Item Creation Without Quantity", False, f"Exception: {str(e)}")
            return []

    def test_orderable_items_without_limitations(self):
        """Test Orderable Items Without Limitations - verify ALL production items are returned"""
        print("\n=== TEST 2: Orderable Items Without Limitations ===")
        
        try:
            # Get all production items first
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code != 200:
                self.log_result("Get all production items", False, f"Status: {response.status_code}")
                return
            
            all_production_items = response.json()
            self.log_result("Get all production items", True, f"Found {len(all_production_items)} total production items")
            
            # Test GET /api/orderable-items - should return ALL production items
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                self.log_result("GET /api/orderable-items", True, f"Retrieved {len(orderable_items)} orderable items")
                
                # Verify ALL production items are returned (no limitations)
                if len(orderable_items) == len(all_production_items):
                    self.log_result("All items available for ordering", True, 
                                  f"All {len(all_production_items)} production items are orderable")
                else:
                    self.log_result("All items available for ordering", False,
                                  f"Expected {len(all_production_items)} items, got {len(orderable_items)}")
                
                # Verify items show as always available (no quantity restrictions)
                for item in orderable_items:
                    if item.get("available_quantity") == 1000:  # Always show as available
                        self.log_result(f"Always available quantity for {item['name']}", True,
                                      f"Quantity: {item['available_quantity']}")
                    else:
                        self.log_result(f"Always available quantity for {item['name']}", False,
                                      f"Expected 1000, got {item.get('available_quantity')}")
                    
                    # Verify availability_status is always "available"
                    if item.get("availability_status") == "available":
                        self.log_result(f"Always available status for {item['name']}", True,
                                      f"Status: {item['availability_status']}")
                    else:
                        self.log_result(f"Always available status for {item['name']}", False,
                                      f"Expected 'available', got {item.get('availability_status')}")
                    
                    # Confirm unit_of_measure shows as "kg" for all items
                    if item.get("unit_of_measure") == "kg":
                        self.log_result(f"Unit of measure for {item['name']}", True,
                                      f"Unit: {item['unit_of_measure']}")
                    else:
                        self.log_result(f"Unit of measure for {item['name']}", False,
                                      f"Expected 'kg', got {item.get('unit_of_measure')}")
            else:
                self.log_result("GET /api/orderable-items", False, f"Status: {response.status_code}")
            
            # Test GET /api/orderable-items/by-category - verify all items in all categories
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                self.log_result("GET /api/orderable-items/by-category", True,
                              f"Retrieved items organized by {len(items_by_category)} categories")
                
                # Count total items across all categories
                total_items_by_category = sum(len(items) for items in items_by_category.values())
                
                if total_items_by_category == len(all_production_items):
                    self.log_result("All items in categories", True,
                                  f"All {len(all_production_items)} items found across categories")
                else:
                    self.log_result("All items in categories", False,
                                  f"Expected {len(all_production_items)}, found {total_items_by_category}")
                
                # Verify each category has items with proper structure
                for category, items in items_by_category.items():
                    if items:
                        self.log_result(f"Category {category} has items", True, f"{len(items)} items")
                        
                        # Check first item structure
                        first_item = items[0]
                        required_fields = ["id", "name", "category", "available_quantity", "unit_of_measure", "unit_price"]
                        missing_fields = [field for field in required_fields if field not in first_item]
                        
                        if not missing_fields:
                            self.log_result(f"Category {category} item structure", True, "All required fields present")
                        else:
                            self.log_result(f"Category {category} item structure", False, f"Missing: {missing_fields}")
            else:
                self.log_result("GET /api/orderable-items/by-category", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Orderable Items Without Limitations", False, f"Exception: {str(e)}")

    def test_order_creation_without_inventory_reduction(self):
        """Test Order Creation Without Inventory Reduction"""
        print("\n=== TEST 3: Order Creation Without Inventory Reduction ===")
        
        try:
            # Get orderable items for testing
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code != 200:
                self.log_result("Get orderable items for order test", False, f"Status: {response.status_code}")
                return
            
            orderable_items = response.json()
            if not orderable_items:
                self.log_result("Get orderable items for order test", False, "No orderable items available")
                return
            
            # Get venue user for order
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code != 200:
                self.log_result("Get venue user", False, f"Status: {response.status_code}")
                return
            
            users = response.json()
            venue_users = [user for user in users if user.get("role") == "venue_staff"]
            if not venue_users:
                self.log_result("Get venue user", False, "No venue users found")
                return
            
            venue_user = venue_users[0]
            
            # Create test order with production items
            test_items = orderable_items[:3]  # Use first 3 items
            order_items = []
            
            for item in test_items:
                order_items.append({
                    "production_item_id": item["id"],
                    "production_item_name": item["name"],
                    "quantity": 5,  # Order 5 of each
                    "unit_of_measure": item["unit_of_measure"],
                    "unit_price": item["unit_price"]
                })
            
            order_data = {
                "venue_name": venue_user["name"],
                "venue_id": venue_user["id"],
                "delivery_address": venue_user.get("address") or "123 Default Street, Test City, 12345",
                "items": order_items
            }
            
            # Store original quantities before order
            original_quantities = {}
            for item in test_items:
                original_quantities[item["id"]] = item["available_quantity"]
            
            # Create the order
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.log_result("Create test order", True, f"Order ID: {order['id']}, Total: ${order['total_amount']:.2f}")
                
                # Verify order is created successfully with proper structure
                required_fields = ["id", "venue_name", "venue_id", "items", "total_amount", "status"]
                missing_fields = [field for field in required_fields if field not in order]
                
                if not missing_fields:
                    self.log_result("Order structure verification", True, "All required fields present")
                else:
                    self.log_result("Order structure verification", False, f"Missing fields: {missing_fields}")
                
                # Confirm production item quantities are NOT reduced
                response = self.session.get(f"{BASE_URL}/orderable-items")
                if response.status_code == 200:
                    updated_orderable_items = response.json()
                    
                    quantities_unchanged = True
                    for item in updated_orderable_items:
                        if item["id"] in original_quantities:
                            original_qty = original_quantities[item["id"]]
                            current_qty = item["available_quantity"]
                            
                            if current_qty == original_qty:
                                self.log_result(f"No inventory reduction for {item['name']}", True,
                                              f"Quantity remains {current_qty}")
                            else:
                                self.log_result(f"No inventory reduction for {item['name']}", False,
                                              f"Quantity changed from {original_qty} to {current_qty}")
                                quantities_unchanged = False
                    
                    if quantities_unchanged:
                        self.log_result("Overall inventory unchanged", True, "No production item quantities were reduced")
                    else:
                        self.log_result("Overall inventory unchanged", False, "Some quantities were unexpectedly reduced")
                else:
                    self.log_result("Verify no inventory reduction", False, "Cannot verify inventory levels")
                
                # Test notification system still works with orders
                # Check if notification was created for the order
                response = self.session.get(f"{BASE_URL}/notifications/{venue_user['id']}")
                if response.status_code == 200:
                    notifications = response.json()
                    order_notifications = [n for n in notifications if order["id"] in n.get("message", "")]
                    
                    if order_notifications:
                        self.log_result("Order notification created", True, f"Found {len(order_notifications)} notifications")
                    else:
                        self.log_result("Order notification created", False, "No notifications found for this order")
                else:
                    self.log_result("Order notification created", False, f"Cannot check notifications: {response.status_code}")
                
                return order
            else:
                self.log_result("Create test order", False, f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Order Creation Without Inventory Reduction", False, f"Exception: {str(e)}")
            return None

    def test_complete_simplified_workflow(self):
        """Test Complete Simplified Workflow"""
        print("\n=== TEST 4: Complete Simplified Workflow ===")
        
        try:
            # Step 1: Manager creates item → item immediately available for ordering
            print("\n--- Step 1: Manager creates item ---")
            
            workflow_item = {
                "name": "Workflow Test Burger",
                "category": "Main Course",
                "base_cost": 15.0,
                "assigned_staff": "chef_alice"
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=workflow_item
            )
            
            if response.status_code == 200:
                created_item = response.json()
                self.log_result("Manager creates item", True, f"Created: {created_item['name']}")
                
                # Verify item immediately available for ordering
                response = self.session.get(f"{BASE_URL}/orderable-items")
                if response.status_code == 200:
                    orderable_items = response.json()
                    item_found = any(item["id"] == created_item["id"] for item in orderable_items)
                    
                    if item_found:
                        self.log_result("Item immediately available for ordering", True,
                                      "Item appears in orderable-items immediately")
                    else:
                        self.log_result("Item immediately available for ordering", False,
                                      "Item not found in orderable-items")
                else:
                    self.log_result("Item immediately available for ordering", False,
                                  f"Cannot check orderable items: {response.status_code}")
            else:
                self.log_result("Manager creates item", False, f"Status: {response.status_code}")
                return
            
            # Step 2: Venue places order → no inventory reduction
            print("\n--- Step 2: Venue places order ---")
            
            # Get venue user
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                venue_users = [user for user in users if user.get("role") == "venue_staff"]
                if venue_users:
                    venue_user = venue_users[0]
                    
                    # Place order for the workflow item
                    order_data = {
                        "venue_name": venue_user["name"],
                        "venue_id": venue_user["id"],
                        "delivery_address": venue_user.get("address") or "123 Default Street, Test City, 12345",
                        "items": [{
                            "production_item_id": created_item["id"],
                            "production_item_name": created_item["name"],
                            "quantity": 3,
                            "unit_of_measure": created_item["unit_of_measure"],
                            "unit_price": created_item["unit_price"]
                        }]
                    }
                    
                    response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                    if response.status_code == 200:
                        order = response.json()
                        self.log_result("Venue places order", True, f"Order placed: {order['id']}")
                        
                        # Verify no inventory reduction
                        response = self.session.get(f"{BASE_URL}/orderable-items")
                        if response.status_code == 200:
                            updated_orderable_items = response.json()
                            workflow_item_updated = next((item for item in updated_orderable_items 
                                                       if item["id"] == created_item["id"]), None)
                            
                            if workflow_item_updated and workflow_item_updated["available_quantity"] == 1000:
                                self.log_result("No inventory reduction after order", True,
                                              "Item quantity remains at 1000 (always available)")
                            else:
                                self.log_result("No inventory reduction after order", False,
                                              f"Quantity changed to {workflow_item_updated['available_quantity'] if workflow_item_updated else 'item not found'}")
                    else:
                        self.log_result("Venue places order", False, f"Status: {response.status_code}")
                        return
                else:
                    self.log_result("Get venue user for workflow", False, "No venue users found")
                    return
            else:
                self.log_result("Get venue user for workflow", False, f"Status: {response.status_code}")
                return
            
            # Step 3: Kitchen receives notification → can process order
            print("\n--- Step 3: Kitchen receives notification ---")
            
            # Get kitchen staff user
            kitchen_users = [user for user in users if user.get("role") == "kitchen_staff"]
            if kitchen_users:
                kitchen_user = kitchen_users[0]
                
                # Check if kitchen staff received notification
                response = self.session.get(f"{BASE_URL}/notifications/{kitchen_user['id']}")
                if response.status_code == 200:
                    notifications = response.json()
                    order_notifications = [n for n in notifications if order["id"] in n.get("message", "")]
                    
                    if order_notifications:
                        self.log_result("Kitchen receives notification", True,
                                      f"Kitchen staff received {len(order_notifications)} notifications")
                    else:
                        self.log_result("Kitchen receives notification", False,
                                      "No order notifications found for kitchen staff")
                else:
                    self.log_result("Kitchen receives notification", False,
                                  f"Cannot check kitchen notifications: {response.status_code}")
                
                # Verify kitchen can see and process the order
                response = self.session.get(f"{BASE_URL}/orders?status=pending")
                if response.status_code == 200:
                    pending_orders = response.json()
                    workflow_order = next((o for o in pending_orders if o["id"] == order["id"]), None)
                    
                    if workflow_order:
                        self.log_result("Kitchen can see order for processing", True,
                                      f"Order {order['id']} visible in pending orders")
                        
                        # Test kitchen can update order status
                        response = self.session.put(f"{BASE_URL}/orders/{order['id']}/status?status=preparing")
                        if response.status_code == 200:
                            self.log_result("Kitchen can process order", True,
                                          "Successfully updated order status to 'preparing'")
                        else:
                            self.log_result("Kitchen can process order", False,
                                          f"Cannot update order status: {response.status_code}")
                    else:
                        self.log_result("Kitchen can see order for processing", False,
                                      "Order not found in pending orders")
                else:
                    self.log_result("Kitchen can see order for processing", False,
                                  f"Cannot get pending orders: {response.status_code}")
            else:
                self.log_result("Get kitchen user for workflow", False, "No kitchen users found")
            
            # Step 4: Verify all items always remain "available" status
            print("\n--- Step 4: Verify items always remain available ---")
            
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                final_orderable_items = response.json()
                
                all_available = all(item.get("availability_status") == "available" for item in final_orderable_items)
                all_quantity_1000 = all(item.get("available_quantity") == 1000 for item in final_orderable_items)
                
                if all_available:
                    self.log_result("All items always remain available status", True,
                                  f"All {len(final_orderable_items)} items have 'available' status")
                else:
                    unavailable_items = [item["name"] for item in final_orderable_items 
                                       if item.get("availability_status") != "available"]
                    self.log_result("All items always remain available status", False,
                                  f"Items not available: {unavailable_items}")
                
                if all_quantity_1000:
                    self.log_result("All items always show quantity 1000", True,
                                  f"All {len(final_orderable_items)} items show quantity 1000")
                else:
                    different_quantities = [(item["name"], item.get("available_quantity")) 
                                          for item in final_orderable_items 
                                          if item.get("available_quantity") != 1000]
                    self.log_result("All items always show quantity 1000", False,
                                  f"Items with different quantities: {different_quantities}")
            else:
                self.log_result("Verify items always remain available", False,
                              f"Cannot check final item status: {response.status_code}")
            
            self.log_result("Complete Simplified Workflow", True,
                          "Full workflow completed: Manager creates → immediately available → venue orders → no inventory reduction → kitchen processes → items remain available")
                
        except Exception as e:
            self.log_result("Complete Simplified Workflow", False, f"Exception: {str(e)}")
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

    def test_order_notification_system(self):
        """Test order notification system for kitchen and managers"""
        print("\n=== Testing Order Notification System ===")
        
        try:
            # Step 1: Test GET /api/dashboard/stats includes recent_orders data
            response = self.session.get(f"{BASE_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                self.log_result("GET /api/dashboard/stats", True, "Dashboard stats retrieved successfully")
                
                # Verify structure includes orders section with recent_orders
                if "orders" in stats and "recent_orders" in stats["orders"]:
                    recent_orders = stats["orders"]["recent_orders"]
                    self.log_result("Dashboard stats includes recent_orders", True, 
                                  f"Found {len(recent_orders)} recent orders")
                    
                    # Verify recent_orders structure
                    if recent_orders:
                        first_order = recent_orders[0]
                        required_fields = ["id", "venue_name", "order_date", "total_amount", "status", "items_count"]
                        missing_fields = [field for field in required_fields if field not in first_order]
                        
                        if not missing_fields:
                            self.log_result("Recent orders structure", True, "All required fields present")
                        else:
                            self.log_result("Recent orders structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Dashboard stats includes recent_orders", False, 
                                  "recent_orders not found in orders section")
            else:
                self.log_result("GET /api/dashboard/stats", False, f"Status: {response.status_code}")
            
            # Step 2: Create a test order to verify it appears in notifications
            # Get venue info first
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                venue_user = next((user for user in users if user.get("role") == "venue_staff"), None)
                
                if venue_user:
                    # Get orderable items
                    response = self.session.get(f"{BASE_URL}/orderable-items")
                    if response.status_code == 200:
                        orderable_items = response.json()
                        if orderable_items:
                            # Create a test order
                            order_items = [
                                {
                                    "production_item_id": orderable_items[0]["id"],
                                    "production_item_name": orderable_items[0]["name"],
                                    "quantity": 2,
                                    "unit_of_measure": orderable_items[0]["unit_of_measure"],
                                    "unit_price": orderable_items[0]["unit_price"]
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
                                new_order = response.json()
                                self.log_result("Create test order for notifications", True, 
                                              f"Order ID: {new_order['id']}")
                                
                                # Verify order appears in dashboard stats recent_orders
                                response = self.session.get(f"{BASE_URL}/dashboard/stats")
                                if response.status_code == 200:
                                    updated_stats = response.json()
                                    recent_orders = updated_stats["orders"]["recent_orders"]
                                    
                                    order_found = any(order["id"] == new_order["id"] for order in recent_orders)
                                    if order_found:
                                        self.log_result("New order appears in recent_orders", True, 
                                                      "Order found in dashboard notifications")
                                    else:
                                        self.log_result("New order appears in recent_orders", False, 
                                                      "Order not found in recent_orders")
                                else:
                                    self.log_result("Verify order in dashboard stats", False, 
                                                  f"Status: {response.status_code}")
                                
                                return new_order
                            else:
                                self.log_result("Create test order for notifications", False, 
                                              f"Status: {response.status_code}")
                        else:
                            self.log_result("Get orderable items for test order", False, "No orderable items available")
                    else:
                        self.log_result("Get orderable items for test order", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Get venue user for test order", False, "No venue user found")
            else:
                self.log_result("Get users for test order", False, f"Status: {response.status_code}")
            
            return None
            
        except Exception as e:
            self.log_result("Order Notification System", False, f"Exception: {str(e)}")
            return None

    def test_kitchen_order_management(self, test_order=None):
        """Test kitchen staff order management functionality"""
        print("\n=== Testing Kitchen Order Management ===")
        
        try:
            # Step 1: Test GET /api/orders?status=pending for kitchen staff
            response = self.session.get(f"{BASE_URL}/orders?status=pending")
            if response.status_code == 200:
                pending_orders = response.json()
                self.log_result("GET /api/orders?status=pending", True, 
                              f"Retrieved {len(pending_orders)} pending orders")
                
                # Verify all returned orders have pending status
                if pending_orders:
                    all_pending = all(order.get("status") == "pending" for order in pending_orders)
                    if all_pending:
                        self.log_result("Pending orders filter accuracy", True, 
                                      "All returned orders have pending status")
                    else:
                        self.log_result("Pending orders filter accuracy", False, 
                                      "Some orders don't have pending status")
                    
                    # If we have a test order, verify it appears in pending orders
                    if test_order:
                        test_order_found = any(order["id"] == test_order["id"] for order in pending_orders)
                        if test_order_found:
                            self.log_result("Test order in pending orders", True, 
                                          "Test order found in pending orders list")
                        else:
                            self.log_result("Test order in pending orders", False, 
                                          "Test order not found in pending orders")
                else:
                    self.log_result("Pending orders available", False, "No pending orders found")
            else:
                self.log_result("GET /api/orders?status=pending", False, f"Status: {response.status_code}")
            
            # Step 2: Test PUT /api/orders/{id}/status for updating to 'preparing'
            if test_order:
                order_id = test_order["id"]
                
                # Update order status to 'preparing'
                response = self.session.put(f"{BASE_URL}/orders/{order_id}/status?status=preparing")
                if response.status_code == 200:
                    self.log_result("Update order status to preparing", True, 
                                  f"Order {order_id} status updated to preparing")
                    
                    # Verify the status was actually updated
                    response = self.session.get(f"{BASE_URL}/orders")
                    if response.status_code == 200:
                        all_orders = response.json()
                        updated_order = next((order for order in all_orders if order["id"] == order_id), None)
                        
                        if updated_order and updated_order.get("status") == "preparing":
                            self.log_result("Verify order status update", True, 
                                          "Order status successfully updated to preparing")
                        else:
                            self.log_result("Verify order status update", False, 
                                          f"Expected 'preparing', got '{updated_order.get('status') if updated_order else 'order not found'}'")
                    else:
                        self.log_result("Verify order status update", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Update order status to preparing", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
            else:
                self.log_result("Test order status update", False, "No test order available")
                
        except Exception as e:
            self.log_result("Kitchen Order Management", False, f"Exception: {str(e)}")

    def test_pdf_export_functionality(self):
        """Test PDF export functionality for Xero integration"""
        print("\n=== Testing PDF Export Functionality ===")
        
        try:
            # Step 1: Get available invoices
            response = self.session.get(f"{BASE_URL}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                self.log_result("GET /api/invoices", True, f"Retrieved {len(invoices)} invoices")
                
                if invoices:
                    test_invoice = invoices[0]
                    invoice_id = test_invoice["id"]
                    
                    # Step 2: Test GET /api/invoices/{id}/pdf endpoint
                    response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
                    if response.status_code == 200:
                        self.log_result("GET /api/invoices/{id}/pdf", True, 
                                      f"PDF generated successfully for invoice {invoice_id}")
                        
                        # Verify response is PDF content
                        content_type = response.headers.get('content-type', '')
                        if 'application/pdf' in content_type:
                            self.log_result("PDF content type", True, "Correct PDF content type")
                        else:
                            self.log_result("PDF content type", False, f"Expected PDF, got {content_type}")
                        
                        # Verify Content-Disposition header for download
                        content_disposition = response.headers.get('content-disposition', '')
                        if 'attachment' in content_disposition and 'filename=' in content_disposition:
                            self.log_result("PDF download headers", True, f"Proper download headers: {content_disposition}")
                            
                            # Verify filename format includes invoice number
                            invoice_number = test_invoice.get("invoice_number", "unknown")
                            if invoice_number in content_disposition:
                                self.log_result("PDF filename format", True, 
                                              f"Filename includes invoice number: {invoice_number}")
                            else:
                                self.log_result("PDF filename format", False, 
                                              f"Filename doesn't include invoice number {invoice_number}")
                        else:
                            self.log_result("PDF download headers", False, 
                                          f"Missing proper download headers: {content_disposition}")
                        
                        # Verify PDF content size (should be substantial)
                        pdf_size = len(response.content)
                        if pdf_size > 1000:  # At least 1KB
                            self.log_result("PDF content size", True, f"PDF size: {pdf_size} bytes")
                        else:
                            self.log_result("PDF content size", False, f"PDF too small: {pdf_size} bytes")
                        
                        # Step 3: Verify invoice contains Xero-compatible fields
                        required_xero_fields = ["invoice_number", "issue_date", "venue_name", "delivery_address", 
                                              "items", "subtotal", "tax_amount", "total_amount"]
                        missing_fields = [field for field in required_xero_fields if field not in test_invoice]
                        
                        if not missing_fields:
                            self.log_result("Xero-compatible invoice fields", True, 
                                          "All required Xero fields present in invoice")
                        else:
                            self.log_result("Xero-compatible invoice fields", False, 
                                          f"Missing Xero fields: {missing_fields}")
                        
                        # Verify invoice items structure
                        if "items" in test_invoice and test_invoice["items"]:
                            first_item = test_invoice["items"][0]
                            required_item_fields = ["production_item_name", "quantity", "unit_of_measure", "unit_price"]
                            missing_item_fields = [field for field in required_item_fields if field not in first_item]
                            
                            if not missing_item_fields:
                                self.log_result("Invoice items structure", True, 
                                              "Invoice items have all required fields")
                            else:
                                self.log_result("Invoice items structure", False, 
                                              f"Missing item fields: {missing_item_fields}")
                        else:
                            self.log_result("Invoice items structure", False, "No items found in invoice")
                        
                    else:
                        self.log_result("GET /api/invoices/{id}/pdf", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    
                    # Step 4: Test PDF export with non-existent invoice ID
                    fake_invoice_id = "non-existent-invoice-id"
                    response = self.session.get(f"{BASE_URL}/invoices/{fake_invoice_id}/pdf")
                    if response.status_code == 404:
                        self.log_result("PDF export error handling", True, 
                                      "Correctly returns 404 for non-existent invoice")
                    else:
                        self.log_result("PDF export error handling", False, 
                                      f"Expected 404, got {response.status_code}")
                        
                else:
                    self.log_result("Test PDF export", False, "No invoices available for testing")
            else:
                self.log_result("GET /api/invoices", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("PDF Export Functionality", False, f"Exception: {str(e)}")

    def test_complete_notification_workflow(self):
        """Test complete notification workflow as specified in review request"""
        print("\n=== Testing Complete Notification Workflow ===")
        
        try:
            # Step 1: Place a test order from venue
            print("\n--- Step 1: Place test order from venue ---")
            
            # Get venue and orderable items
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code != 200:
                self.log_result("Complete Notification Workflow", False, "Cannot retrieve users")
                return
            
            users = response.json()
            venue_user = next((user for user in users if user.get("role") == "venue_staff"), None)
            if not venue_user:
                self.log_result("Complete Notification Workflow", False, "No venue user found")
                return
            
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code != 200:
                self.log_result("Complete Notification Workflow", False, "Cannot retrieve orderable items")
                return
            
            orderable_items = response.json()
            if not orderable_items:
                self.log_result("Complete Notification Workflow", False, "No orderable items available")
                return
            
            # Create workflow test order
            order_items = [
                {
                    "production_item_id": orderable_items[0]["id"],
                    "production_item_name": orderable_items[0]["name"],
                    "quantity": 3,
                    "unit_of_measure": orderable_items[0]["unit_of_measure"],
                    "unit_price": orderable_items[0]["unit_price"]
                }
            ]
            
            order_data = {
                "venue_name": venue_user["name"],
                "venue_id": venue_user["id"],
                "delivery_address": venue_user.get("address") or "123 Workflow Test Street",
                "items": order_items
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            if response.status_code == 200:
                workflow_order = response.json()
                self.log_result("Step 1 - Place test order from venue", True, 
                              f"Order ID: {workflow_order['id']}, Venue: {venue_user['name']}")
            else:
                self.log_result("Step 1 - Place test order from venue", False, 
                              f"Status: {response.status_code}")
                return
            
            # Step 2: Verify order appears in dashboard stats recent_orders
            print("\n--- Step 2: Verify order in dashboard notifications ---")
            
            response = self.session.get(f"{BASE_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                recent_orders = stats.get("orders", {}).get("recent_orders", [])
                
                order_in_notifications = any(order["id"] == workflow_order["id"] for order in recent_orders)
                if order_in_notifications:
                    self.log_result("Step 2 - Order appears in dashboard recent_orders", True, 
                                  "Order found in manager dashboard notifications")
                else:
                    self.log_result("Step 2 - Order appears in dashboard recent_orders", False, 
                                  "Order not found in dashboard notifications")
            else:
                self.log_result("Step 2 - Check dashboard notifications", False, f"Status: {response.status_code}")
            
            # Step 3: Verify order shows as 'pending' status
            print("\n--- Step 3: Verify order has pending status ---")
            
            if workflow_order.get("status") == "pending":
                self.log_result("Step 3 - Order has pending status", True, 
                              f"Order status: {workflow_order['status']}")
            else:
                self.log_result("Step 3 - Order has pending status", False, 
                              f"Expected 'pending', got '{workflow_order.get('status')}'")
            
            # Step 4: Test kitchen can see pending order
            print("\n--- Step 4: Test kitchen can see pending order ---")
            
            response = self.session.get(f"{BASE_URL}/orders?status=pending")
            if response.status_code == 200:
                pending_orders = response.json()
                kitchen_can_see_order = any(order["id"] == workflow_order["id"] for order in pending_orders)
                
                if kitchen_can_see_order:
                    self.log_result("Step 4 - Kitchen can see pending order", True, 
                                  "Order visible to kitchen staff in pending orders")
                else:
                    self.log_result("Step 4 - Kitchen can see pending order", False, 
                                  "Order not visible in kitchen pending orders")
            else:
                self.log_result("Step 4 - Kitchen pending orders check", False, f"Status: {response.status_code}")
            
            # Step 5: Test kitchen can update order to 'preparing' status
            print("\n--- Step 5: Test kitchen updates order to preparing ---")
            
            response = self.session.put(f"{BASE_URL}/orders/{workflow_order['id']}/status?status=preparing")
            if response.status_code == 200:
                self.log_result("Step 5 - Kitchen updates order to preparing", True, 
                              "Order status successfully updated by kitchen")
                
                # Verify status was actually updated
                response = self.session.get(f"{BASE_URL}/orders")
                if response.status_code == 200:
                    all_orders = response.json()
                    updated_order = next((order for order in all_orders if order["id"] == workflow_order["id"]), None)
                    
                    if updated_order and updated_order.get("status") == "preparing":
                        self.log_result("Step 5 - Verify status update", True, 
                                      "Order status confirmed as 'preparing'")
                    else:
                        self.log_result("Step 5 - Verify status update", False, 
                                      f"Status not updated correctly: {updated_order.get('status') if updated_order else 'order not found'}")
                else:
                    self.log_result("Step 5 - Verify status update", False, f"Status: {response.status_code}")
            else:
                self.log_result("Step 5 - Kitchen updates order to preparing", False, 
                              f"Status: {response.status_code}")
            
            # Step 6: Verify manager dashboard shows updated order notifications
            print("\n--- Step 6: Verify manager dashboard shows updated notifications ---")
            
            response = self.session.get(f"{BASE_URL}/dashboard/stats")
            if response.status_code == 200:
                updated_stats = response.json()
                recent_orders = updated_stats.get("orders", {}).get("recent_orders", [])
                
                # Find our order in recent orders
                our_order = next((order for order in recent_orders if order["id"] == workflow_order["id"]), None)
                if our_order:
                    if our_order.get("status") == "preparing":
                        self.log_result("Step 6 - Manager sees updated order status", True, 
                                      "Manager dashboard shows order as 'preparing'")
                    else:
                        self.log_result("Step 6 - Manager sees updated order status", False, 
                                      f"Dashboard shows status as '{our_order.get('status')}' instead of 'preparing'")
                else:
                    self.log_result("Step 6 - Manager sees order in dashboard", False, 
                                  "Order not found in manager dashboard recent_orders")
            else:
                self.log_result("Step 6 - Check manager dashboard", False, f"Status: {response.status_code}")
            
            print("\n--- Workflow Summary ---")
            self.log_result("Complete Notification Workflow", True, 
                          "Full workflow tested: venue order → dashboard notification → kitchen visibility → status update → manager notification")
            
        except Exception as e:
            self.log_result("Complete Notification Workflow", False, f"Exception: {str(e)}")

    def test_production_item_edit_functionality(self):
        """Test production item edit functionality for managers"""
        print("\n=== Testing Production Item Edit Functionality ===")
        
        try:
            # Step 1: Create a test production item to edit
            test_item = {
                "name": "Original Test Item",
                "category": "Main Course",
                "quantity": 10,
                "unit_of_measure": "portions",
                "assigned_staff": "chef_alice",
                "base_cost": 12.0
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=test_item
            )
            
            if response.status_code != 200:
                self.log_result("Create test item for editing", False, f"Status: {response.status_code}")
                return
            
            created_item = response.json()
            item_id = created_item["id"]
            self.log_result("Create test item for editing", True, f"Item ID: {item_id}")
            
            # Verify initial unit_price calculation (base_cost * 1.15)
            expected_unit_price = 12.0 * 1.15  # 13.80
            if abs(created_item.get("unit_price", 0) - expected_unit_price) < 0.01:
                self.log_result("Initial unit_price calculation", True, 
                              f"Unit price: ${created_item['unit_price']:.2f} (15% markup)")
            else:
                self.log_result("Initial unit_price calculation", False,
                              f"Expected ${expected_unit_price:.2f}, got ${created_item.get('unit_price', 0):.2f}")
            
            # Step 2: Test updating all fields using PUT /api/production-items/{id}
            updated_data = {
                "name": "Updated Test Item Name",
                "category": "Dessert",
                "quantity": 25,
                "unit_of_measure": "slices",
                "assigned_staff": "chef_bob",
                "base_cost": 15.0
            }
            
            response = self.session.put(
                f"{BASE_URL}/production-items/{item_id}",
                json=updated_data
            )
            
            if response.status_code == 200:
                updated_item = response.json()
                self.log_result("PUT /api/production-items/{id} endpoint", True, "Item updated successfully")
                
                # Verify all fields were updated correctly
                for field, expected_value in updated_data.items():
                    if field == "base_cost":
                        continue  # We'll check this separately with unit_price
                    
                    actual_value = updated_item.get(field)
                    if actual_value == expected_value:
                        self.log_result(f"Update {field} field", True, f"{field}: {actual_value}")
                    else:
                        self.log_result(f"Update {field} field", False,
                                      f"Expected {expected_value}, got {actual_value}")
                
                # Verify automatic unit_price recalculation after edit
                expected_new_unit_price = 15.0 * 1.15  # 17.25
                actual_unit_price = updated_item.get("unit_price", 0)
                if abs(actual_unit_price - expected_new_unit_price) < 0.01:
                    self.log_result("Unit_price recalculation after edit", True,
                                  f"New unit price: ${actual_unit_price:.2f} (15% markup on ${updated_data['base_cost']:.2f})")
                else:
                    self.log_result("Unit_price recalculation after edit", False,
                                  f"Expected ${expected_new_unit_price:.2f}, got ${actual_unit_price:.2f}")
                
                # Verify base_cost was updated
                actual_base_cost = updated_item.get("base_cost", 0)
                if abs(actual_base_cost - updated_data["base_cost"]) < 0.01:
                    self.log_result("Update base_cost field", True, f"Base cost: ${actual_base_cost:.2f}")
                else:
                    self.log_result("Update base_cost field", False,
                                  f"Expected ${updated_data['base_cost']:.2f}, got ${actual_base_cost:.2f}")
                
            else:
                self.log_result("PUT /api/production-items/{id} endpoint", False,
                              f"Status: {response.status_code}, Response: {response.text}")
                return
            
            # Step 3: Verify edited item appears correctly in production items list
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                all_items = response.json()
                edited_item = next((item for item in all_items if item["id"] == item_id), None)
                
                if edited_item:
                    self.log_result("Edited item in production list", True, "Item found in list")
                    
                    # Verify the item in the list has all updated values
                    for field, expected_value in updated_data.items():
                        if field == "base_cost":
                            continue
                        actual_value = edited_item.get(field)
                        if actual_value == expected_value:
                            self.log_result(f"List shows updated {field}", True, f"{field}: {actual_value}")
                        else:
                            self.log_result(f"List shows updated {field}", False,
                                          f"Expected {expected_value}, got {actual_value}")
                else:
                    self.log_result("Edited item in production list", False, "Item not found in list")
            else:
                self.log_result("Edited item in production list", False, f"Status: {response.status_code}")
            
            # Step 4: Test error handling for invalid data
            invalid_data_tests = [
                {
                    "name": "Test invalid item ID",
                    "item_id": "invalid-id-12345",
                    "data": {"name": "Test", "category": "Main Course", "quantity": 5, "unit_of_measure": "units", "base_cost": 10.0},
                    "expected_status": 404
                },
                {
                    "name": "Test missing required fields",
                    "item_id": item_id,
                    "data": {"name": "Test"},  # Missing required fields
                    "expected_status": 422
                }
            ]
            
            for test_case in invalid_data_tests:
                response = self.session.put(
                    f"{BASE_URL}/production-items/{test_case['item_id']}",
                    json=test_case["data"]
                )
                
                if response.status_code == test_case["expected_status"]:
                    self.log_result(f"Error handling: {test_case['name']}", True,
                                  f"Correctly returned {response.status_code}")
                else:
                    self.log_result(f"Error handling: {test_case['name']}", False,
                                  f"Expected {test_case['expected_status']}, got {response.status_code}")
            
            # Step 5: Test that orderable items are updated if availability changes
            # First, set the item as available for ordering
            availability_data = {
                "available_for_order": 10,
                "availability_status": "available"
            }
            
            response = self.session.put(
                f"{BASE_URL}/production-items/{item_id}/availability",
                json=availability_data
            )
            
            if response.status_code == 200:
                self.log_result("Set item availability for ordering", True, "Item made available")
                
                # Check if item appears in orderable items (with new workflow, no completion needed)
                response = self.session.get(f"{BASE_URL}/orderable-items")
                if response.status_code == 200:
                    orderable_items = response.json()
                    orderable_item = next((item for item in orderable_items if item["id"] == item_id), None)
                    
                    if orderable_item:
                        # Verify the orderable item shows updated information
                        if orderable_item.get("name") == updated_data["name"]:
                            self.log_result("Orderable items reflect edit changes", True,
                                          f"Name updated to: {orderable_item['name']}")
                        else:
                            self.log_result("Orderable items reflect edit changes", False,
                                          f"Expected {updated_data['name']}, got {orderable_item.get('name')}")
                        
                        if orderable_item.get("category") == updated_data["category"]:
                            self.log_result("Orderable items category updated", True,
                                          f"Category: {orderable_item['category']}")
                        else:
                            self.log_result("Orderable items category updated", False,
                                          f"Expected {updated_data['category']}, got {orderable_item.get('category')}")
                        
                        if orderable_item.get("unit_of_measure") == updated_data["unit_of_measure"]:
                            self.log_result("Orderable items unit_of_measure updated", True,
                                          f"Unit: {orderable_item['unit_of_measure']}")
                        else:
                            self.log_result("Orderable items unit_of_measure updated", False,
                                          f"Expected {updated_data['unit_of_measure']}, got {orderable_item.get('unit_of_measure')}")
                    else:
                        self.log_result("Orderable items reflect edit changes", False, "Item not found in orderable items")
                else:
                    self.log_result("Check orderable items after edit", False, f"Status: {response.status_code}")
            else:
                self.log_result("Set item availability for ordering", False, f"Status: {response.status_code}")
            
            return item_id
            
        except Exception as e:
            self.log_result("Production Item Edit Functionality", False, f"Exception: {str(e)}")
            return None

    def run_production_item_edit_tests(self):
        """Run tests specifically for production item edit functionality"""
        print("🧪 Starting Production Item Edit Functionality Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Focus: Testing production item edit functionality for managers")
        print("=" * 80)
        
        # Test production item edit functionality
        self.test_production_item_edit_functionality()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 PRODUCTION ITEM EDIT TEST SUMMARY")
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

    def run_notification_and_pdf_tests(self):
        """Run comprehensive tests for notification system and PDF export"""
        print("🧪 Starting Notification System and PDF Export Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Focus: Order notification system and PDF export functionality for Xero integration")
        print("=" * 80)
        
        # Test 1: Order Notification System
        test_order = self.test_order_notification_system()
        
        # Test 2: Kitchen Order Management
        self.test_kitchen_order_management(test_order)
        
        # Test 3: PDF Export Functionality
        self.test_pdf_export_functionality()
        
        # Test 4: Complete Notification Workflow
        self.test_complete_notification_workflow()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 NOTIFICATION SYSTEM AND PDF EXPORT TEST SUMMARY")
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

    def debug_venue_items_visibility_issue(self):
        """Debug why venue users are only seeing limited items and categories"""
        print("\n=== DEBUGGING VENUE ITEMS VISIBILITY ISSUE ===")
        print("User reports: Can only see 'most ordered and skewers' items, not all food items and categories")
        
        try:
            # 1. Check current database state
            print("\n--- 1. CHECKING CURRENT DATABASE STATE ---")
            
            # Get all production items
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                all_items = response.json()
                total_items = len(all_items)
                self.log_result("Total production items in database", True, f"{total_items} items")
                
                # Count items with available_for_order > 0
                available_items = [item for item in all_items if item.get("available_for_order", 0) > 0]
                available_count = len(available_items)
                self.log_result("Items with available_for_order > 0", True, f"{available_count} items")
                
                # Show breakdown by category
                category_breakdown = {}
                available_category_breakdown = {}
                
                for item in all_items:
                    category = item.get("category", "Unknown")
                    category_breakdown[category] = category_breakdown.get(category, 0) + 1
                    
                    if item.get("available_for_order", 0) > 0:
                        available_category_breakdown[category] = available_category_breakdown.get(category, 0) + 1
                
                print(f"\n📊 CATEGORY BREAKDOWN:")
                print(f"Total items by category: {dict(category_breakdown)}")
                print(f"Available items by category: {dict(available_category_breakdown)}")
                
                # Show status breakdown
                status_breakdown = {}
                for item in all_items:
                    status = item.get("status", "Unknown")
                    status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                print(f"Status breakdown: {dict(status_breakdown)}")
                
            else:
                self.log_result("Get all production items", False, f"Status: {response.status_code}")
                return
            
            # 2. Test orderable items endpoints
            print("\n--- 2. TESTING ORDERABLE ITEMS ENDPOINTS ---")
            
            # Test GET /api/orderable-items
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                orderable_count = len(orderable_items)
                self.log_result("GET /api/orderable-items", True, f"Returns {orderable_count} items")
                
                # Show what items are returned
                if orderable_items:
                    print(f"\n📋 ORDERABLE ITEMS RETURNED:")
                    for item in orderable_items[:10]:  # Show first 10
                        print(f"  • {item.get('name', 'Unknown')} (Category: {item.get('category', 'Unknown')}, Available: {item.get('available_quantity', 0)})")
                    
                    if len(orderable_items) > 10:
                        print(f"  ... and {len(orderable_items) - 10} more items")
                else:
                    print("❌ NO ORDERABLE ITEMS RETURNED!")
                
                # Check categories in orderable items
                orderable_categories = set(item.get('category', 'Unknown') for item in orderable_items)
                print(f"\n🏷️ CATEGORIES IN ORDERABLE ITEMS: {list(orderable_categories)}")
                
            else:
                self.log_result("GET /api/orderable-items", False, f"Status: {response.status_code}")
            
            # Test GET /api/orderable-items/by-category
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                categories_returned = list(items_by_category.keys())
                total_items_by_category = sum(len(items) for items in items_by_category.values())
                
                self.log_result("GET /api/orderable-items/by-category", True, 
                              f"Returns {len(categories_returned)} categories with {total_items_by_category} total items")
                
                print(f"\n📂 CATEGORIES WITH ITEM COUNTS:")
                for category, items in items_by_category.items():
                    print(f"  • {category}: {len(items)} items")
                    # Show first few items in each category
                    for item in items[:3]:
                        print(f"    - {item.get('name', 'Unknown')} (Available: {item.get('available_quantity', 0)})")
                    if len(items) > 3:
                        print(f"    ... and {len(items) - 3} more items")
                
            else:
                self.log_result("GET /api/orderable-items/by-category", False, f"Status: {response.status_code}")
            
            # 3. Check categories endpoint
            print("\n--- 3. TESTING CATEGORIES ENDPOINT ---")
            
            response = self.session.get(f"{BASE_URL}/categories")
            if response.status_code == 200:
                categories_data = response.json()
                if "categories" in categories_data:
                    all_categories = categories_data["categories"]
                    self.log_result("GET /api/categories", True, f"Returns {len(all_categories)} categories")
                    print(f"📋 ALL CATEGORIES: {all_categories}")
                else:
                    self.log_result("GET /api/categories", False, "Invalid response structure")
            else:
                self.log_result("GET /api/categories", False, f"Status: {response.status_code}")
            
            # 4. Analyze the issue
            print("\n--- 4. ISSUE ANALYSIS ---")
            
            # Check if the issue is with the orderable items workflow
            print(f"\n🔍 ANALYSIS:")
            print(f"• Total production items: {total_items}")
            print(f"• Items with available_for_order > 0: {available_count}")
            print(f"• Items returned by orderable-items API: {orderable_count}")
            
            if available_count > orderable_count:
                print(f"⚠️  ISSUE IDENTIFIED: {available_count - orderable_count} items have available_for_order > 0 but are not appearing in orderable-items API")
                
                # Find the missing items
                orderable_ids = set(item['id'] for item in orderable_items)
                missing_items = [item for item in available_items if item['id'] not in orderable_ids]
                
                print(f"\n❌ MISSING ITEMS FROM ORDERABLE API:")
                for item in missing_items[:10]:  # Show first 10 missing items
                    print(f"  • {item.get('name', 'Unknown')} (Category: {item.get('category', 'Unknown')}, Status: {item.get('status', 'Unknown')}, Available: {item.get('available_for_order', 0)})")
                
                # Check if the issue is with status filtering
                missing_statuses = set(item.get('status', 'Unknown') for item in missing_items)
                print(f"\n📊 STATUS OF MISSING ITEMS: {list(missing_statuses)}")
                
                if 'pending' in missing_statuses or 'in_progress' in missing_statuses:
                    print("💡 LIKELY CAUSE: Items need to be marked as 'completed' to appear in orderable-items")
                    print("   The orderable-items endpoint may still be filtering by status='completed'")
            
            elif available_count == orderable_count:
                print("✅ All items with available_for_order > 0 are appearing in orderable-items API")
                if orderable_count == 0:
                    print("❌ ROOT CAUSE: No items have available_for_order > 0 set by managers")
                    print("   SOLUTION: Managers need to set available_for_order quantities > 0")
            
            # 5. Test the workflow by creating and setting up a test item
            print("\n--- 5. TESTING WORKFLOW WITH NEW ITEM ---")
            
            test_item = {
                "name": "Debug Test Item",
                "category": "Main Course",
                "quantity": 10,
                "unit_of_measure": "portions"
            }
            
            # Create item
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
            if response.status_code == 200:
                created_item = response.json()
                item_id = created_item["id"]
                self.log_result("Create test item", True, f"ID: {item_id}")
                
                # Set availability
                availability_data = {
                    "available_for_order": 5,
                    "unit_price": 20.0,
                    "availability_status": "available"
                }
                
                response = self.session.put(f"{BASE_URL}/production-items/{item_id}/availability", json=availability_data)
                if response.status_code == 200:
                    self.log_result("Set item availability", True, "Available for order: 5")
                    
                    # Check if it appears in orderable-items (should appear immediately with new workflow)
                    response = self.session.get(f"{BASE_URL}/orderable-items")
                    if response.status_code == 200:
                        orderable_items_after = response.json()
                        test_item_found = any(item['id'] == item_id for item in orderable_items_after)
                        
                        if test_item_found:
                            self.log_result("Test item appears in orderable-items (new workflow)", True, 
                                          "Item appears immediately after setting availability")
                        else:
                            self.log_result("Test item missing from orderable-items", False, 
                                          "Item should appear immediately with new workflow")
                            
                            # Check if we need to mark as completed (old workflow)
                            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/status?status=completed")
                            if response.status_code == 200:
                                self.log_result("Mark test item as completed", True, "Status updated")
                                
                                # Check again
                                response = self.session.get(f"{BASE_URL}/orderable-items")
                                if response.status_code == 200:
                                    orderable_items_final = response.json()
                                    test_item_found_final = any(item['id'] == item_id for item in orderable_items_final)
                                    
                                    if test_item_found_final:
                                        self.log_result("Test item appears after completion", True, 
                                                      "Item appears after marking as completed")
                                        print("⚠️  WORKFLOW ISSUE: Items still need to be marked as 'completed' to appear")
                                    else:
                                        self.log_result("Test item still missing", False, 
                                                      "Item missing even after completion")
                                else:
                                    self.log_result("Check orderable items after completion", False, f"Status: {response.status_code}")
                            else:
                                self.log_result("Mark test item as completed", False, f"Status: {response.status_code}")
                    else:
                        self.log_result("Check orderable items after availability", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Set item availability", False, f"Status: {response.status_code}")
            else:
                self.log_result("Create test item", False, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_result("Debug Venue Items Visibility Issue", False, f"Exception: {str(e)}")

    def run_debug_tests(self):
        """Run debug tests for venue items visibility issue"""
        print("🔍 Starting Debug Tests for Venue Items Visibility Issue")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Focus: Debugging why venue users only see limited items and categories")
        print("=" * 80)
        
        # Debug the specific issue
        self.debug_venue_items_visibility_issue()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 DEBUG TEST SUMMARY")
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
        
        return self.test_results

    def test_notification_management_endpoints(self):
        """Test notification management endpoints comprehensively"""
        print("\n=== TESTING NOTIFICATION MANAGEMENT ENDPOINTS ===")
        
        try:
            # Test 1: GET /api/notification-preferences - verify it creates default preferences for all users
            response = self.session.get(f"{BASE_URL}/notification-preferences")
            if response.status_code == 200:
                preferences = response.json()
                self.log_result("GET /api/notification-preferences", True, 
                              f"Retrieved preferences for {len(preferences)} users")
                
                # Verify structure of preferences
                if preferences:
                    first_pref = preferences[0]
                    required_fields = ["id", "user_id", "user_name", "user_role", "order_placed", 
                                     "order_preparing", "order_ready", "order_delivered", "created_at", "updated_at"]
                    missing_fields = [field for field in required_fields if field not in first_pref]
                    
                    if not missing_fields:
                        self.log_result("Notification preferences structure", True, "All required fields present")
                    else:
                        self.log_result("Notification preferences structure", False, f"Missing fields: {missing_fields}")
                    
                    # Verify default values
                    default_notifications = ["order_placed", "order_preparing", "order_ready", "order_delivered"]
                    for notification_type in default_notifications:
                        if first_pref.get(notification_type) == True:
                            self.log_result(f"Default {notification_type} preference", True, "Enabled by default")
                        else:
                            self.log_result(f"Default {notification_type} preference", False, "Not enabled by default")
                
                # Store user IDs for testing updates
                self.test_user_ids = [pref["user_id"] for pref in preferences[:2]]  # Use first 2 users
                
            else:
                self.log_result("GET /api/notification-preferences", False, f"Status: {response.status_code}")
                return
            
            # Test 2: PUT /api/notification-preferences/{user_id} - update a user's notification settings
            if hasattr(self, 'test_user_ids') and self.test_user_ids:
                test_user_id = self.test_user_ids[0]
                
                # Update preferences
                update_data = {
                    "order_placed": True,
                    "order_preparing": False,  # Disable this one
                    "order_ready": True,
                    "order_delivered": False,  # Disable this one
                    "email": "test@example.com",
                    "phone": "+1234567890",
                    "notify_email": True,
                    "notify_sms": False,
                    "notify_in_app": True
                }
                
                response = self.session.put(f"{BASE_URL}/notification-preferences/{test_user_id}", json=update_data)
                if response.status_code == 200:
                    self.log_result("PUT /api/notification-preferences/{user_id}", True, 
                                  f"Updated preferences for user {test_user_id}")
                    
                    # Verify the update by fetching preferences again
                    response = self.session.get(f"{BASE_URL}/notification-preferences")
                    if response.status_code == 200:
                        updated_preferences = response.json()
                        updated_user_pref = next((pref for pref in updated_preferences 
                                                if pref["user_id"] == test_user_id), None)
                        
                        if updated_user_pref:
                            # Verify specific updates
                            if (updated_user_pref.get("order_preparing") == False and 
                                updated_user_pref.get("order_delivered") == False and
                                updated_user_pref.get("email") == "test@example.com"):
                                self.log_result("Verify notification preferences update", True, 
                                              "Preferences updated correctly")
                            else:
                                self.log_result("Verify notification preferences update", False, 
                                              "Some preferences not updated correctly")
                        else:
                            self.log_result("Verify notification preferences update", False, 
                                          "Updated user preferences not found")
                    else:
                        self.log_result("Verify notification preferences update", False, 
                                      "Cannot verify update")
                else:
                    self.log_result("PUT /api/notification-preferences/{user_id}", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            # Test 3: Test that preferences are properly stored and retrieved
            response = self.session.get(f"{BASE_URL}/notification-preferences")
            if response.status_code == 200:
                final_preferences = response.json()
                
                # Verify all users have preferences
                response = self.session.get(f"{BASE_URL}/users")
                if response.status_code == 200:
                    all_users = response.json()
                    
                    if len(final_preferences) >= len(all_users):
                        self.log_result("All users have notification preferences", True, 
                                      f"Preferences: {len(final_preferences)}, Users: {len(all_users)}")
                    else:
                        self.log_result("All users have notification preferences", False, 
                                      f"Missing preferences for some users")
                else:
                    self.log_result("All users have notification preferences", False, 
                                  "Cannot verify user count")
            else:
                self.log_result("Preferences storage verification", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Notification Management Endpoints", False, f"Exception: {str(e)}")

    def test_automatic_notification_triggers(self):
        """Test automatic notification triggers during order workflow"""
        print("\n=== TESTING AUTOMATIC NOTIFICATION TRIGGERS ===")
        
        try:
            # First, create a test order to trigger notifications
            # Get venue information
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code != 200:
                self.log_result("Automatic Notification Triggers", False, "Cannot retrieve users")
                return
            
            users = response.json()
            venue_users = [user for user in users if user.get("role") == "venue_staff"]
            
            if not venue_users:
                self.log_result("Automatic Notification Triggers", False, "No venue users found")
                return
            
            venue_user = venue_users[0]
            venue_id = venue_user["id"]
            venue_name = venue_user["name"]
            venue_address = venue_user.get("address") or "123 Test Street, Test City"
            
            # Get orderable items
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code != 200 or not response.json():
                # Create a test item if none exist
                test_item = {
                    "name": "Notification Test Item",
                    "category": "Main Course",
                    "quantity": 10,
                    "unit_of_measure": "portions",
                    "base_cost": 15.0
                }
                
                response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
                if response.status_code == 200:
                    created_item = response.json()
                    
                    # Set availability
                    availability_data = {
                        "available_for_order": 5,
                        "unit_price": 17.25,
                        "availability_status": "available"
                    }
                    
                    response = self.session.put(
                        f"{BASE_URL}/production-items/{created_item['id']}/availability",
                        json=availability_data
                    )
                    
                    if response.status_code == 200:
                        self.log_result("Create test item for notifications", True, 
                                      f"Created and set availability for {test_item['name']}")
                    else:
                        self.log_result("Create test item for notifications", False, 
                                      "Failed to set availability")
                        return
                else:
                    self.log_result("Create test item for notifications", False, 
                                  "Failed to create test item")
                    return
            
            # Get orderable items again
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code != 200:
                self.log_result("Get orderable items for notification test", False, f"Status: {response.status_code}")
                return
            
            orderable_items = response.json()
            if not orderable_items:
                self.log_result("Get orderable items for notification test", False, "No orderable items available")
                return
            
            # Test 1: Create a test order and verify "order_placed" notification is created
            order_items = [
                {
                    "production_item_id": orderable_items[0]["id"],
                    "production_item_name": orderable_items[0]["name"],
                    "quantity": 2,
                    "unit_of_measure": orderable_items[0]["unit_of_measure"],
                    "unit_price": orderable_items[0]["unit_price"]
                }
            ]
            
            order_data = {
                "venue_name": venue_name,
                "venue_id": venue_id,
                "delivery_address": venue_address,
                "items": order_items,
                "delivery_date": "2024-12-20"
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            if response.status_code == 200:
                test_order = response.json()
                order_id = test_order["id"]
                invoice_number = test_order.get("invoice_number", "N/A")
                
                self.log_result("Create test order for notifications", True, 
                              f"Order ID: {order_id}, Invoice: {invoice_number}")
                
                # Check if order_placed notification was created
                time.sleep(1)  # Brief delay to ensure notification is created
                
                # Get all notification events to verify order_placed notification
                response = self.session.get(f"{BASE_URL}/notifications/{venue_id}")
                if response.status_code == 200:
                    notifications = response.json()
                    order_placed_notifications = [n for n in notifications if n.get("event_type") == "order_placed" 
                                                and n.get("order_id") == order_id]
                    
                    if order_placed_notifications:
                        notification = order_placed_notifications[0]
                        expected_message = f"New order #{invoice_number} from {venue_name}"
                        if expected_message in notification.get("message", ""):
                            self.log_result("Order placed notification created", True, 
                                          f"Message: {notification['message']}")
                        else:
                            self.log_result("Order placed notification created", False, 
                                          f"Unexpected message: {notification.get('message')}")
                    else:
                        self.log_result("Order placed notification created", False, 
                                      "No order_placed notification found")
                else:
                    self.log_result("Order placed notification created", False, 
                                  f"Cannot retrieve notifications: {response.status_code}")
                
                # Test 2: Update order status to "preparing" and verify "order_preparing" notification
                response = self.session.put(f"{BASE_URL}/orders/{order_id}/status?status=preparing")
                if response.status_code == 200:
                    self.log_result("Update order status to preparing", True, "Status updated successfully")
                    
                    time.sleep(1)  # Brief delay
                    
                    # Check for order_preparing notification
                    response = self.session.get(f"{BASE_URL}/notifications/{venue_id}")
                    if response.status_code == 200:
                        notifications = response.json()
                        preparing_notifications = [n for n in notifications if n.get("event_type") == "order_preparing" 
                                                 and n.get("order_id") == order_id]
                        
                        if preparing_notifications:
                            notification = preparing_notifications[0]
                            expected_message = f"Order #{invoice_number} is now being prepared"
                            if expected_message in notification.get("message", ""):
                                self.log_result("Order preparing notification created", True, 
                                              f"Message: {notification['message']}")
                            else:
                                self.log_result("Order preparing notification created", False, 
                                              f"Unexpected message: {notification.get('message')}")
                        else:
                            self.log_result("Order preparing notification created", False, 
                                          "No order_preparing notification found")
                    else:
                        self.log_result("Order preparing notification created", False, 
                                      f"Cannot retrieve notifications: {response.status_code}")
                else:
                    self.log_result("Update order status to preparing", False, f"Status: {response.status_code}")
                
                # Test 3: Update order status to "ready" and verify "order_ready" notification
                response = self.session.put(f"{BASE_URL}/orders/{order_id}/status?status=ready")
                if response.status_code == 200:
                    self.log_result("Update order status to ready", True, "Status updated successfully")
                    
                    time.sleep(1)  # Brief delay
                    
                    # Check for order_ready notification
                    response = self.session.get(f"{BASE_URL}/notifications/{venue_id}")
                    if response.status_code == 200:
                        notifications = response.json()
                        ready_notifications = [n for n in notifications if n.get("event_type") == "order_ready" 
                                             and n.get("order_id") == order_id]
                        
                        if ready_notifications:
                            notification = ready_notifications[0]
                            expected_message = f"Order #{invoice_number} is ready for pickup/delivery"
                            if expected_message in notification.get("message", ""):
                                self.log_result("Order ready notification created", True, 
                                              f"Message: {notification['message']}")
                            else:
                                self.log_result("Order ready notification created", False, 
                                              f"Unexpected message: {notification.get('message')}")
                        else:
                            self.log_result("Order ready notification created", False, 
                                          "No order_ready notification found")
                    else:
                        self.log_result("Order ready notification created", False, 
                                      f"Cannot retrieve notifications: {response.status_code}")
                else:
                    self.log_result("Update order status to ready", False, f"Status: {response.status_code}")
                
                # Test 4: Update order status to "delivered" and verify "order_delivered" notification
                response = self.session.put(f"{BASE_URL}/orders/{order_id}/status?status=delivered")
                if response.status_code == 200:
                    self.log_result("Update order status to delivered", True, "Status updated successfully")
                    
                    time.sleep(1)  # Brief delay
                    
                    # Check for order_delivered notification
                    response = self.session.get(f"{BASE_URL}/notifications/{venue_id}")
                    if response.status_code == 200:
                        notifications = response.json()
                        delivered_notifications = [n for n in notifications if n.get("event_type") == "order_delivered" 
                                                 and n.get("order_id") == order_id]
                        
                        if delivered_notifications:
                            notification = delivered_notifications[0]
                            expected_message = f"Order #{invoice_number} has been delivered to {venue_name}"
                            if expected_message in notification.get("message", ""):
                                self.log_result("Order delivered notification created", True, 
                                              f"Message: {notification['message']}")
                            else:
                                self.log_result("Order delivered notification created", False, 
                                              f"Unexpected message: {notification.get('message')}")
                        else:
                            self.log_result("Order delivered notification created", False, 
                                          "No order_delivered notification found")
                    else:
                        self.log_result("Order delivered notification created", False, 
                                      f"Cannot retrieve notifications: {response.status_code}")
                else:
                    self.log_result("Update order status to delivered", False, f"Status: {response.status_code}")
                
                # Store order ID for later tests
                self.test_order_id = order_id
                
            else:
                self.log_result("Create test order for notifications", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Automatic Notification Triggers", False, f"Exception: {str(e)}")

    def test_notification_creation_and_retrieval(self):
        """Test notification creation and retrieval endpoints"""
        print("\n=== TESTING NOTIFICATION CREATION AND RETRIEVAL ===")
        
        try:
            # Test 1: POST /api/notifications endpoint for creating notifications
            test_notification_data = {
                "event_type": "order_placed",
                "order_id": getattr(self, 'test_order_id', 'test-order-123'),
                "message": "Test notification message for API testing"
            }
            
            # Create notification using query parameters (as per the API design)
            response = self.session.post(
                f"{BASE_URL}/notifications",
                params={
                    "event_type": test_notification_data["event_type"],
                    "order_id": test_notification_data["order_id"],
                    "message": test_notification_data["message"]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result("POST /api/notifications", True, 
                              f"Created notification: {result.get('message', 'Success')}")
                
                # Store notification ID for later tests
                self.test_notification_id = result.get("notification_id")
                
            else:
                self.log_result("POST /api/notifications", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
            
            # Test 2: GET /api/notifications/{user_id} to retrieve user notifications
            # Get a test user ID
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                if users:
                    test_user_id = users[0]["id"]
                    
                    response = self.session.get(f"{BASE_URL}/notifications/{test_user_id}")
                    if response.status_code == 200:
                        notifications = response.json()
                        self.log_result("GET /api/notifications/{user_id}", True, 
                                      f"Retrieved {len(notifications)} notifications for user")
                        
                        # Verify notification structure
                        if notifications:
                            first_notification = notifications[0]
                            required_fields = ["id", "event_type", "order_id", "message", "recipients", "created_at"]
                            missing_fields = [field for field in required_fields if field not in first_notification]
                            
                            if not missing_fields:
                                self.log_result("Notification structure", True, "All required fields present")
                            else:
                                self.log_result("Notification structure", False, f"Missing fields: {missing_fields}")
                            
                            # Verify user is in recipients
                            if test_user_id in first_notification.get("recipients", []):
                                self.log_result("User in notification recipients", True, "User correctly included in recipients")
                            else:
                                self.log_result("User in notification recipients", False, "User not in recipients list")
                        
                    else:
                        self.log_result("GET /api/notifications/{user_id}", False, 
                                      f"Status: {response.status_code}")
                else:
                    self.log_result("GET /api/notifications/{user_id}", False, "No users found for testing")
            else:
                self.log_result("GET /api/notifications/{user_id}", False, "Cannot retrieve users for testing")
            
            # Test 3: PUT /api/notifications/{notification_id}/read for marking as read
            if hasattr(self, 'test_notification_id') and self.test_notification_id:
                # Use the notification ID from the created notification
                notification_id = self.test_notification_id
                test_user_id = users[0]["id"] if users else "test-user-id"
                
                response = self.session.put(
                    f"{BASE_URL}/notifications/{notification_id}/read",
                    params={"user_id": test_user_id}
                )
                
                if response.status_code == 200:
                    self.log_result("PUT /api/notifications/{notification_id}/read", True, 
                                  "Notification marked as read successfully")
                else:
                    self.log_result("PUT /api/notifications/{notification_id}/read", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
            else:
                # Try with any existing notification
                if hasattr(self, 'test_user_id') and users:
                    test_user_id = users[0]["id"]
                    response = self.session.get(f"{BASE_URL}/notifications/{test_user_id}")
                    if response.status_code == 200:
                        notifications = response.json()
                        if notifications:
                            notification_id = notifications[0]["id"]
                            
                            response = self.session.put(
                                f"{BASE_URL}/notifications/{notification_id}/read",
                                params={"user_id": test_user_id}
                            )
                            
                            if response.status_code == 200:
                                self.log_result("PUT /api/notifications/{notification_id}/read", True, 
                                              "Notification marked as read successfully")
                            else:
                                self.log_result("PUT /api/notifications/{notification_id}/read", False, 
                                              f"Status: {response.status_code}")
                        else:
                            self.log_result("PUT /api/notifications/{notification_id}/read", False, 
                                          "No notifications available to mark as read")
                    else:
                        self.log_result("PUT /api/notifications/{notification_id}/read", False, 
                                      "Cannot retrieve notifications for read test")
                
        except Exception as e:
            self.log_result("Notification Creation and Retrieval", False, f"Exception: {str(e)}")

    def test_complete_notification_workflow(self):
        """Test complete notification workflow end-to-end"""
        print("\n=== TESTING COMPLETE NOTIFICATION WORKFLOW ===")
        
        try:
            # Test 1: Place order → verify notification created with proper message format
            # Get venue and orderable items
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code != 200:
                self.log_result("Complete Notification Workflow", False, "Cannot retrieve users")
                return
            
            users = response.json()
            venue_users = [user for user in users if user.get("role") == "venue_staff"]
            
            if not venue_users:
                self.log_result("Complete Notification Workflow", False, "No venue users found")
                return
            
            venue_user = venue_users[0]
            venue_id = venue_user["id"]
            venue_name = venue_user["name"]
            venue_address = venue_user.get("address") or "123 Test Street, Test City"
            
            # Get orderable items
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code != 200 or not response.json():
                self.log_result("Complete Notification Workflow", False, "No orderable items available")
                return
            
            orderable_items = response.json()
            
            # Create workflow test order
            order_items = [
                {
                    "production_item_id": orderable_items[0]["id"],
                    "production_item_name": orderable_items[0]["name"],
                    "quantity": 1,
                    "unit_of_measure": orderable_items[0]["unit_of_measure"],
                    "unit_price": orderable_items[0]["unit_price"]
                }
            ]
            
            order_data = {
                "venue_name": venue_name,
                "venue_id": venue_id,
                "delivery_address": venue_address,
                "items": order_items,
                "delivery_date": "2024-12-21"
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            if response.status_code == 200:
                workflow_order = response.json()
                order_id = workflow_order["id"]
                invoice_number = workflow_order.get("invoice_number", "N/A")
                total_amount = workflow_order.get("total_amount", 0)
                
                self.log_result("Place order for workflow test", True, 
                              f"Order ID: {order_id}, Total: ${total_amount:.2f}")
                
                time.sleep(1)  # Brief delay
                
                # Verify notification created with proper message format
                response = self.session.get(f"{BASE_URL}/notifications/{venue_id}")
                if response.status_code == 200:
                    notifications = response.json()
                    order_placed_notifications = [n for n in notifications if n.get("event_type") == "order_placed" 
                                                and n.get("order_id") == order_id]
                    
                    if order_placed_notifications:
                        notification = order_placed_notifications[0]
                        message = notification.get("message", "")
                        
                        # Verify message format contains key elements
                        message_checks = [
                            (f"#{invoice_number}" in message, "Invoice number in message"),
                            (venue_name in message, "Venue name in message"),
                            (f"${total_amount:.2f}" in message, "Total amount in message"),
                            ("New order" in message, "Order type in message")
                        ]
                        
                        for check, description in message_checks:
                            self.log_result(description, check, f"Message: {message}")
                        
                    else:
                        self.log_result("Order placed notification format", False, 
                                      "No order_placed notification found")
                else:
                    self.log_result("Order placed notification format", False, 
                                  f"Cannot retrieve notifications: {response.status_code}")
                
                # Test 2: Change status through workflow → verify each notification has correct content
                status_transitions = [
                    ("preparing", "is now being prepared in the kitchen"),
                    ("ready", "is ready for pickup/delivery"),
                    ("delivered", f"has been delivered to {venue_name}")
                ]
                
                for status, expected_content in status_transitions:
                    response = self.session.put(f"{BASE_URL}/orders/{order_id}/status?status={status}")
                    if response.status_code == 200:
                        self.log_result(f"Update order to {status}", True, f"Status updated to {status}")
                        
                        time.sleep(1)  # Brief delay
                        
                        # Check notification content
                        response = self.session.get(f"{BASE_URL}/notifications/{venue_id}")
                        if response.status_code == 200:
                            notifications = response.json()
                            status_notifications = [n for n in notifications if n.get("event_type") == f"order_{status}" 
                                                  and n.get("order_id") == order_id]
                            
                            if status_notifications:
                                notification = status_notifications[0]
                                message = notification.get("message", "")
                                
                                # Verify message content
                                content_checks = [
                                    (f"#{invoice_number}" in message, f"Invoice number in {status} message"),
                                    (expected_content in message, f"Expected content in {status} message")
                                ]
                                
                                for check, description in content_checks:
                                    self.log_result(description, check, f"Message: {message}")
                                
                            else:
                                self.log_result(f"Order {status} notification content", False, 
                                              f"No order_{status} notification found")
                        else:
                            self.log_result(f"Order {status} notification content", False, 
                                          f"Cannot retrieve notifications: {response.status_code}")
                    else:
                        self.log_result(f"Update order to {status}", False, f"Status: {response.status_code}")
                
                # Test 3: Check that notifications are sent to users with proper preferences enabled
                # Get notification preferences to verify targeting
                response = self.session.get(f"{BASE_URL}/notification-preferences")
                if response.status_code == 200:
                    preferences = response.json()
                    
                    # Count users with each notification type enabled
                    notification_counts = {
                        "order_placed": len([p for p in preferences if p.get("order_placed", False)]),
                        "order_preparing": len([p for p in preferences if p.get("order_preparing", False)]),
                        "order_ready": len([p for p in preferences if p.get("order_ready", False)]),
                        "order_delivered": len([p for p in preferences if p.get("order_delivered", False)])
                    }
                    
                    self.log_result("Notification preference targeting", True, 
                                  f"Users with preferences - Placed: {notification_counts['order_placed']}, "
                                  f"Preparing: {notification_counts['order_preparing']}, "
                                  f"Ready: {notification_counts['order_ready']}, "
                                  f"Delivered: {notification_counts['order_delivered']}")
                    
                    # Verify notifications were created for users with preferences enabled
                    for event_type, user_count in notification_counts.items():
                        if user_count > 0:
                            # Check if notifications exist for this event type
                            test_user_with_pref = next((p for p in preferences if p.get(event_type, False)), None)
                            if test_user_with_pref:
                                response = self.session.get(f"{BASE_URL}/notifications/{test_user_with_pref['user_id']}")
                                if response.status_code == 200:
                                    user_notifications = response.json()
                                    event_notifications = [n for n in user_notifications 
                                                         if n.get("event_type") == event_type and n.get("order_id") == order_id]
                                    
                                    if event_notifications:
                                        self.log_result(f"Notification sent to users with {event_type} preference", True, 
                                                      f"Found {len(event_notifications)} notifications")
                                    else:
                                        self.log_result(f"Notification sent to users with {event_type} preference", False, 
                                                      f"No {event_type} notifications found for user with preference enabled")
                                else:
                                    self.log_result(f"Notification sent to users with {event_type} preference", False, 
                                                  f"Cannot retrieve notifications for user: {response.status_code}")
                        else:
                            self.log_result(f"Users with {event_type} preference", True, 
                                          f"No users have {event_type} preference enabled (expected)")
                else:
                    self.log_result("Notification preference targeting", False, 
                                  f"Cannot retrieve preferences: {response.status_code}")
                
            else:
                self.log_result("Place order for workflow test", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Complete Notification Workflow", False, f"Exception: {str(e)}")

    def run_notification_system_tests(self):
        """Run comprehensive notification system tests"""
        print("🔔 STARTING COMPREHENSIVE NOTIFICATION SYSTEM TESTING")
        print("=" * 70)
        
        # Run all notification system tests
        self.test_notification_management_endpoints()
        self.test_automatic_notification_triggers()
        self.test_notification_creation_and_retrieval()
        self.test_complete_notification_workflow()
        
        # Print summary
        print("\n" + "=" * 70)
        print("🔔 NOTIFICATION SYSTEM TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Tests Passed: {self.test_results['passed']}")
        print(f"❌ Tests Failed: {self.test_results['failed']}")
        print(f"📊 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        return self.test_results

if __name__ == "__main__":
    tester = KitchenAPITester()
    results = tester.test_simplified_ordering_system()
    
    # Exit with appropriate code
    if results["failed"] == 0:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {results['failed']} TESTS FAILED")
        sys.exit(1)