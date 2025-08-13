#!/usr/bin/env python3
"""
Backend API Testing for Updated Production Item Workflow and Delete Functionality
Focus: Testing the updated orderable items workflow and production item delete functionality

Key Changes to Test:
1. Updated Orderable Items Workflow - items are now orderable as soon as available_for_order > 0 (no more 'completed' status requirement)
2. Production Item Delete Functionality - DELETE endpoint with protection for items referenced in orders

Test Plan:
1. Test GET /api/orderable-items returns items based ONLY on available_for_order > 0
2. Test GET /api/orderable-items/by-category works the same way
3. Create test item, set availability > 0 but leave status as 'pending', confirm it appears in orderable items
4. Test DELETE /api/production-items/{id} works for items not referenced in orders
5. Test DELETE /api/production-items/{id} returns 400 error for items referenced in orders
6. Test complete workflow: Manager creates item → sets availability → item appears in orderable-items (regardless of completion status)
"""

import requests
import json
from datetime import datetime, date, timedelta
import time
import sys

# Backend URL from frontend/.env
BASE_URL = "https://order-flow-6.preview.emergentagent.com/api"

class UpdatedWorkflowTester:
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
    
    def test_updated_orderable_items_workflow(self):
        """Test that orderable items now appear based ONLY on available_for_order > 0, not completion status"""
        print("\n=== Testing Updated Orderable Items Workflow ===")
        
        try:
            # Step 1: Create a test production item
            test_item_data = {
                "name": "Workflow Test Item - Pending Status",
                "category": "Main Course",
                "quantity": 20,
                "unit_of_measure": "portions",
                "base_cost": 12.0
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=test_item_data
            )
            
            if response.status_code != 200:
                self.log_result("Create test item for workflow", False, f"Status: {response.status_code}")
                return None
            
            created_item = response.json()
            item_id = created_item["id"]
            self.log_result("Create test item for workflow", True, f"Item ID: {item_id}, Status: {created_item.get('status', 'unknown')}")
            
            # Verify item starts with status 'pending' and available_for_order = 0
            if created_item.get("status") == "pending" and created_item.get("available_for_order") == 0:
                self.log_result("Initial item state verification", True, "Status: pending, available_for_order: 0")
            else:
                self.log_result("Initial item state verification", False, 
                              f"Status: {created_item.get('status')}, available_for_order: {created_item.get('available_for_order')}")
            
            # Step 2: Verify item does NOT appear in orderable items (available_for_order = 0)
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                item_found = any(item["id"] == item_id for item in orderable_items)
                
                if not item_found:
                    self.log_result("Item not orderable when available_for_order = 0", True, "Item correctly not in orderable items")
                else:
                    self.log_result("Item not orderable when available_for_order = 0", False, "Item incorrectly appears in orderable items")
            else:
                self.log_result("Check orderable items (step 2)", False, f"Status: {response.status_code}")
            
            # Step 3: Set available_for_order > 0 while keeping status as 'pending'
            availability_update = {
                "available_for_order": 15,
                "base_cost": 12.0,
                "availability_status": "available"
            }
            
            response = self.session.put(
                f"{BASE_URL}/production-items/{item_id}/availability",
                json=availability_update
            )
            
            if response.status_code == 200:
                self.log_result("Set availability while status pending", True, "Available_for_order set to 15")
            else:
                self.log_result("Set availability while status pending", False, f"Status: {response.status_code}")
                return None
            
            # Step 4: Verify item NOW appears in orderable items (even though status is still 'pending')
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                found_item = next((item for item in orderable_items if item["id"] == item_id), None)
                
                if found_item:
                    self.log_result("Item orderable when available_for_order > 0 (status still pending)", True, 
                                  f"Item appears in orderable items with quantity: {found_item.get('available_quantity')}")
                    
                    # Verify the item has correct data structure
                    required_fields = ["id", "name", "category", "available_quantity", "unit_of_measure", "unit_price", "availability_status"]
                    missing_fields = [field for field in required_fields if field not in found_item]
                    
                    if not missing_fields:
                        self.log_result("Orderable item structure", True, "All required fields present")
                    else:
                        self.log_result("Orderable item structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Item orderable when available_for_order > 0 (status still pending)", False, 
                                  "Item does not appear in orderable items despite available_for_order > 0")
            else:
                self.log_result("Check orderable items (step 4)", False, f"Status: {response.status_code}")
            
            # Step 5: Test GET /api/orderable-items/by-category works the same way
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                
                # Find our item in the category structure
                item_found_in_category = False
                for category, items in items_by_category.items():
                    if any(item["id"] == item_id for item in items):
                        item_found_in_category = True
                        self.log_result("Item in orderable-items/by-category (status pending)", True, 
                                      f"Found in category: {category}")
                        break
                
                if not item_found_in_category:
                    self.log_result("Item in orderable-items/by-category (status pending)", False, 
                                  "Item not found in by-category endpoint")
            else:
                self.log_result("Check orderable-items/by-category", False, f"Status: {response.status_code}")
            
            # Step 6: Verify the item's actual status is still 'pending' in production items
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                production_items = response.json()
                production_item = next((item for item in production_items if item["id"] == item_id), None)
                
                if production_item and production_item.get("status") == "pending":
                    self.log_result("Production item status remains pending", True, 
                                  "Status is still 'pending' while item is orderable")
                else:
                    self.log_result("Production item status remains pending", False, 
                                  f"Status: {production_item.get('status') if production_item else 'item not found'}")
            else:
                self.log_result("Check production item status", False, f"Status: {response.status_code}")
            
            return item_id
            
        except Exception as e:
            self.log_result("Updated Orderable Items Workflow", False, f"Exception: {str(e)}")
            return None
    
    def test_production_item_delete_functionality(self, test_item_id=None):
        """Test DELETE /api/production-items/{id} functionality with order protection"""
        print("\n=== Testing Production Item Delete Functionality ===")
        
        try:
            # Step 1: Create a test item that we can safely delete (not referenced in orders)
            deletable_item_data = {
                "name": "Deletable Test Item",
                "category": "Dessert",
                "quantity": 10,
                "unit_of_measure": "pieces",
                "base_cost": 8.0
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=deletable_item_data
            )
            
            if response.status_code != 200:
                self.log_result("Create deletable test item", False, f"Status: {response.status_code}")
                return
            
            deletable_item = response.json()
            deletable_item_id = deletable_item["id"]
            self.log_result("Create deletable test item", True, f"Item ID: {deletable_item_id}")
            
            # Step 2: Test successful deletion of item not referenced in orders
            response = self.session.delete(f"{BASE_URL}/production-items/{deletable_item_id}")
            
            if response.status_code == 200:
                response_data = response.json()
                if "message" in response_data and "deleted successfully" in response_data["message"]:
                    self.log_result("Delete item not in orders", True, "Item deleted successfully")
                else:
                    self.log_result("Delete item not in orders", False, f"Unexpected response: {response_data}")
            else:
                self.log_result("Delete item not in orders", False, f"Status: {response.status_code}, Response: {response.text}")
            
            # Step 3: Verify item is actually deleted
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                production_items = response.json()
                deleted_item_found = any(item["id"] == deletable_item_id for item in production_items)
                
                if not deleted_item_found:
                    self.log_result("Verify item deletion", True, "Item no longer exists in production items")
                else:
                    self.log_result("Verify item deletion", False, "Item still exists after deletion")
            else:
                self.log_result("Verify item deletion", False, f"Cannot verify deletion: {response.status_code}")
            
            # Step 4: Create an item and place an order with it to test deletion protection
            ordered_item_data = {
                "name": "Item With Order Reference",
                "category": "Main Course",
                "quantity": 20,
                "unit_of_measure": "portions",
                "base_cost": 15.0
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=ordered_item_data
            )
            
            if response.status_code != 200:
                self.log_result("Create item for order test", False, f"Status: {response.status_code}")
                return
            
            ordered_item = response.json()
            ordered_item_id = ordered_item["id"]
            self.log_result("Create item for order test", True, f"Item ID: {ordered_item_id}")
            
            # Set availability for the item
            availability_update = {
                "available_for_order": 10,
                "base_cost": 15.0,
                "availability_status": "available"
            }
            
            response = self.session.put(
                f"{BASE_URL}/production-items/{ordered_item_id}/availability",
                json=availability_update
            )
            
            if response.status_code != 200:
                self.log_result("Set availability for order test item", False, f"Status: {response.status_code}")
                return
            
            self.log_result("Set availability for order test item", True, "Availability set")
            
            # Get venue user for placing order
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code != 200:
                self.log_result("Get venue user for order", False, f"Status: {response.status_code}")
                return
            
            users = response.json()
            venue_user = next((user for user in users if user.get("role") == "venue_staff"), None)
            
            if not venue_user:
                self.log_result("Get venue user for order", False, "No venue user found")
                return
            
            # Place an order with this item
            order_data = {
                "venue_name": venue_user["name"],
                "venue_id": venue_user["id"],
                "delivery_address": venue_user.get("address") or "123 Test Street",
                "items": [
                    {
                        "production_item_id": ordered_item_id,
                        "production_item_name": ordered_item["name"],
                        "quantity": 2,
                        "unit_of_measure": ordered_item["unit_of_measure"],
                        "unit_price": 17.25  # 15.0 * 1.15 markup
                    }
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                self.log_result("Place order with test item", True, f"Order ID: {order['id']}")
            else:
                self.log_result("Place order with test item", False, f"Status: {response.status_code}")
                return
            
            # Step 5: Test that deletion is now protected (should return 400 error)
            response = self.session.delete(f"{BASE_URL}/production-items/{ordered_item_id}")
            
            if response.status_code == 400:
                response_data = response.json()
                if "detail" in response_data and "referenced in" in response_data["detail"]:
                    self.log_result("Delete protection for ordered item", True, 
                                  f"Correctly blocked deletion: {response_data['detail']}")
                else:
                    self.log_result("Delete protection for ordered item", False, 
                                  f"Wrong error message: {response_data}")
            else:
                self.log_result("Delete protection for ordered item", False, 
                              f"Expected 400, got {response.status_code}, Response: {response.text}")
            
            # Step 6: Verify item still exists after failed deletion attempt
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                production_items = response.json()
                protected_item_found = any(item["id"] == ordered_item_id for item in production_items)
                
                if protected_item_found:
                    self.log_result("Verify protected item still exists", True, "Item correctly preserved after blocked deletion")
                else:
                    self.log_result("Verify protected item still exists", False, "Item was incorrectly deleted despite protection")
            else:
                self.log_result("Verify protected item still exists", False, f"Cannot verify: {response.status_code}")
            
            # Step 7: Test deletion of non-existent item (should return 404)
            fake_item_id = "non-existent-item-id-12345"
            response = self.session.delete(f"{BASE_URL}/production-items/{fake_item_id}")
            
            if response.status_code == 404:
                self.log_result("Delete non-existent item returns 404", True, "Correctly returns 404 for non-existent item")
            else:
                self.log_result("Delete non-existent item returns 404", False, f"Expected 404, got {response.status_code}")
            
        except Exception as e:
            self.log_result("Production Item Delete Functionality", False, f"Exception: {str(e)}")
    
    def test_complete_updated_workflow(self):
        """Test the complete updated workflow: Manager creates item → sets availability → item appears in orderable-items (regardless of completion status)"""
        print("\n=== Testing Complete Updated Workflow ===")
        
        try:
            # Step 1: Manager creates production item
            workflow_item_data = {
                "name": "Complete Workflow Test Item",
                "category": "Appetizer",
                "quantity": 25,
                "unit_of_measure": "pieces",
                "base_cost": 10.0,
                "assigned_staff": "chef_alice"
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=workflow_item_data
            )
            
            if response.status_code != 200:
                self.log_result("Manager creates production item", False, f"Status: {response.status_code}")
                return
            
            workflow_item = response.json()
            item_id = workflow_item["id"]
            self.log_result("Manager creates production item", True, 
                          f"Item: {workflow_item['name']}, Status: {workflow_item.get('status')}")
            
            # Verify item starts as 'pending' and not orderable
            if workflow_item.get("status") == "pending" and workflow_item.get("available_for_order") == 0:
                self.log_result("Initial item state (pending, not orderable)", True, 
                              "Item correctly starts as pending with available_for_order = 0")
            else:
                self.log_result("Initial item state (pending, not orderable)", False, 
                              f"Unexpected initial state: status={workflow_item.get('status')}, available_for_order={workflow_item.get('available_for_order')}")
            
            # Step 2: Manager sets availability (item should become orderable immediately)
            availability_data = {
                "available_for_order": 20,
                "base_cost": 10.0,
                "availability_status": "available"
            }
            
            response = self.session.put(
                f"{BASE_URL}/production-items/{item_id}/availability",
                json=availability_data
            )
            
            if response.status_code == 200:
                self.log_result("Manager sets availability", True, "Availability set to 20 units")
            else:
                self.log_result("Manager sets availability", False, f"Status: {response.status_code}")
                return
            
            # Step 3: Verify item appears in orderable-items immediately (without needing completion)
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                found_item = next((item for item in orderable_items if item["id"] == item_id), None)
                
                if found_item:
                    self.log_result("Item appears in orderable-items (still pending)", True, 
                                  f"Item orderable with quantity: {found_item.get('available_quantity')}")
                    
                    # Verify correct pricing (base_cost * 1.15 markup)
                    expected_price = 10.0 * 1.15  # 11.50
                    actual_price = found_item.get("unit_price")
                    
                    if abs(actual_price - expected_price) < 0.01:
                        self.log_result("Correct pricing with 15% markup", True, f"Price: ${actual_price}")
                    else:
                        self.log_result("Correct pricing with 15% markup", False, 
                                      f"Expected ${expected_price}, got ${actual_price}")
                else:
                    self.log_result("Item appears in orderable-items (still pending)", False, 
                                  "Item not found in orderable items despite availability > 0")
            else:
                self.log_result("Check orderable-items", False, f"Status: {response.status_code}")
            
            # Step 4: Verify item also appears in by-category endpoint
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                
                # Look for our item in the Appetizer category
                appetizer_items = items_by_category.get("Appetizer", [])
                found_in_category = any(item["id"] == item_id for item in appetizer_items)
                
                if found_in_category:
                    self.log_result("Item in by-category endpoint (still pending)", True, 
                                  f"Found in Appetizer category with {len(appetizer_items)} total items")
                else:
                    self.log_result("Item in by-category endpoint (still pending)", False, 
                                  "Item not found in by-category endpoint")
            else:
                self.log_result("Check by-category endpoint", False, f"Status: {response.status_code}")
            
            # Step 5: Verify production item status is still 'pending'
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                production_items = response.json()
                production_item = next((item for item in production_items if item["id"] == item_id), None)
                
                if production_item and production_item.get("status") == "pending":
                    self.log_result("Production status remains pending while orderable", True, 
                                  "Item is orderable but production status is still pending")
                else:
                    self.log_result("Production status remains pending while orderable", False, 
                                  f"Status: {production_item.get('status') if production_item else 'item not found'}")
            else:
                self.log_result("Check production status", False, f"Status: {response.status_code}")
            
            # Step 6: Place an order to verify the workflow works end-to-end
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                venue_user = next((user for user in users if user.get("role") == "venue_staff"), None)
                
                if venue_user:
                    order_data = {
                        "venue_name": venue_user["name"],
                        "venue_id": venue_user["id"],
                        "delivery_address": venue_user.get("address") or "123 Test Street",
                        "items": [
                            {
                                "production_item_id": item_id,
                                "production_item_name": workflow_item["name"],
                                "quantity": 3,
                                "unit_of_measure": workflow_item["unit_of_measure"],
                                "unit_price": 11.50  # 10.0 * 1.15
                            }
                        ]
                    }
                    
                    response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                    
                    if response.status_code == 200:
                        order = response.json()
                        self.log_result("Place order with pending item", True, 
                                      f"Order placed successfully: {order['id']}")
                        
                        # Verify quantity was reduced
                        response = self.session.get(f"{BASE_URL}/orderable-items")
                        if response.status_code == 200:
                            updated_orderable = response.json()
                            updated_item = next((item for item in updated_orderable if item["id"] == item_id), None)
                            
                            if updated_item and updated_item.get("available_quantity") == 17:  # 20 - 3
                                self.log_result("Quantity reduction after order", True, 
                                              f"Quantity reduced from 20 to {updated_item['available_quantity']}")
                            else:
                                self.log_result("Quantity reduction after order", False, 
                                              f"Expected 17, got {updated_item.get('available_quantity') if updated_item else 'item not found'}")
                    else:
                        self.log_result("Place order with pending item", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Get venue user for order test", False, "No venue user found")
            else:
                self.log_result("Get users for order test", False, f"Status: {response.status_code}")
            
            # Step 7: Kitchen can now see the item to produce (verify it's in production items for kitchen staff)
            response = self.session.get(f"{BASE_URL}/production-items?status=pending")
            if response.status_code == 200:
                pending_items = response.json()
                kitchen_item = next((item for item in pending_items if item["id"] == item_id), None)
                
                if kitchen_item:
                    self.log_result("Kitchen can see item to produce", True, 
                                  f"Item visible to kitchen staff with status: {kitchen_item.get('status')}")
                else:
                    self.log_result("Kitchen can see item to produce", False, "Item not found in pending items for kitchen")
            else:
                self.log_result("Check kitchen visibility", False, f"Status: {response.status_code}")
            
            # Step 8: Kitchen marks item as completed
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/status?status=completed")
            
            if response.status_code == 200:
                self.log_result("Kitchen marks item completed", True, "Item marked as completed")
                
                # Verify item is still orderable after completion
                response = self.session.get(f"{BASE_URL}/orderable-items")
                if response.status_code == 200:
                    orderable_after_completion = response.json()
                    still_orderable = any(item["id"] == item_id for item in orderable_after_completion)
                    
                    if still_orderable:
                        self.log_result("Item remains orderable after completion", True, 
                                      "Item continues to be orderable after kitchen completion")
                    else:
                        self.log_result("Item remains orderable after completion", False, 
                                      "Item disappeared from orderable items after completion")
            else:
                self.log_result("Kitchen marks item completed", False, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_result("Complete Updated Workflow", False, f"Exception: {str(e)}")
    
    def test_venue_users_can_see_items_immediately(self):
        """Test that venue users can see items immediately when managers set availability"""
        print("\n=== Testing Venue Users Can See Items Immediately ===")
        
        try:
            # Create a new item for this test
            immediate_item_data = {
                "name": "Immediate Visibility Test Item",
                "category": "Beverage",
                "quantity": 30,
                "unit_of_measure": "cups",
                "base_cost": 5.0
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=immediate_item_data
            )
            
            if response.status_code != 200:
                self.log_result("Create item for immediate visibility test", False, f"Status: {response.status_code}")
                return
            
            immediate_item = response.json()
            item_id = immediate_item["id"]
            self.log_result("Create item for immediate visibility test", True, f"Item ID: {item_id}")
            
            # Verify item is NOT visible to venues initially
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_before = response.json()
                visible_before = any(item["id"] == item_id for item in orderable_before)
                
                if not visible_before:
                    self.log_result("Item not visible before availability set", True, "Item correctly not visible initially")
                else:
                    self.log_result("Item not visible before availability set", False, "Item incorrectly visible before availability set")
            
            # Manager sets availability
            availability_data = {
                "available_for_order": 25,
                "base_cost": 5.0,
                "availability_status": "available"
            }
            
            response = self.session.put(
                f"{BASE_URL}/production-items/{item_id}/availability",
                json=availability_data
            )
            
            if response.status_code != 200:
                self.log_result("Manager sets availability for immediate visibility", False, f"Status: {response.status_code}")
                return
            
            self.log_result("Manager sets availability for immediate visibility", True, "Availability set")
            
            # Verify item is IMMEDIATELY visible to venues (without waiting for completion)
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_after = response.json()
                visible_after = any(item["id"] == item_id for item in orderable_after)
                
                if visible_after:
                    self.log_result("Item immediately visible after availability set", True, 
                                  "Venue users can see item immediately when manager sets availability")
                else:
                    self.log_result("Item immediately visible after availability set", False, 
                                  "Item not visible to venues despite availability being set")
            else:
                self.log_result("Check immediate visibility", False, f"Status: {response.status_code}")
            
            # Verify the same for by-category endpoint
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                beverage_items = items_by_category.get("Beverage", [])
                visible_in_category = any(item["id"] == item_id for item in beverage_items)
                
                if visible_in_category:
                    self.log_result("Item immediately visible in by-category", True, 
                                  "Item appears in by-category endpoint immediately")
                else:
                    self.log_result("Item immediately visible in by-category", False, 
                                  "Item not visible in by-category endpoint")
            else:
                self.log_result("Check by-category immediate visibility", False, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_result("Venue Users Can See Items Immediately", False, f"Exception: {str(e)}")
    
    def run_updated_workflow_tests(self):
        """Run comprehensive tests for the updated workflow and delete functionality"""
        print("🧪 Starting Updated Production Item Workflow and Delete Functionality Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Focus: Updated orderable items workflow (no completion requirement) and delete protection")
        print("=" * 80)
        
        # Test 1: Updated Orderable Items Workflow
        test_item_id = self.test_updated_orderable_items_workflow()
        
        # Test 2: Production Item Delete Functionality
        self.test_production_item_delete_functionality(test_item_id)
        
        # Test 3: Complete Updated Workflow
        self.test_complete_updated_workflow()
        
        # Test 4: Venue Users Can See Items Immediately
        self.test_venue_users_can_see_items_immediately()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 UPDATED WORKFLOW AND DELETE FUNCTIONALITY TEST SUMMARY")
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
    tester = UpdatedWorkflowTester()
    success = tester.run_updated_workflow_tests()
    sys.exit(0 if success else 1)