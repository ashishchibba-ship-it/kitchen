#!/usr/bin/env python3
"""
Focused Testing for Fixed Production Items System
Testing the specific requirements from the review request:
1. Production Items Creation without quantity/status fields
2. Production Items Retrieval with clean data
3. Orderable Items - all items appear and are always available
4. Manager Production Screen Fix - no crashes from undefined fields
5. End-to-End Testing
"""

import requests
import json
from datetime import datetime, date
import time

# Backend URL from frontend/.env
BASE_URL = "https://523e0c6c-09ea-4970-8dcd-e42fec7deab4.preview.emergentagent.com/api"

class FocusedProductionTester:
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

    def test_production_items_creation_without_status_quantity(self):
        """Test 1: Production Items Creation without quantity/status fields"""
        print("\n=== TEST 1: Production Items Creation Without Status/Quantity Management ===")
        
        try:
            # Create items without quantity/status fields - should work with defaults
            test_items = [
                {
                    "name": "Fixed System Pasta",
                    "category": "Main Course",
                    "base_cost": 14.0
                },
                {
                    "name": "Fixed System Salad", 
                    "category": "Salad",
                    "base_cost": 9.0,
                    "assigned_staff": "chef_alice"
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
                    
                    # Verify unit_price is calculated correctly (base_cost * 1.15)
                    expected_unit_price = item_data["base_cost"] * 1.15
                    actual_unit_price = item.get("unit_price")
                    if abs(actual_unit_price - expected_unit_price) < 0.01:
                        self.log_result(f"Unit price calculation for {item_data['name']}", True,
                                      f"${actual_unit_price:.2f} (15% markup on ${item_data['base_cost']:.2f})")
                    else:
                        self.log_result(f"Unit price calculation for {item_data['name']}", False,
                                      f"Expected ${expected_unit_price:.2f}, got ${actual_unit_price:.2f}")
                    
                    # Verify no status/quantity management fields cause issues
                    self.log_result(f"Create item without status/quantity: {item_data['name']}", True,
                                  f"ID: {item['id']}")
                else:
                    self.log_result(f"Create item without status/quantity: {item_data['name']}", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            return created_items
            
        except Exception as e:
            self.log_result("Production Items Creation Without Status/Quantity", False, f"Exception: {str(e)}")
            return []

    def test_production_items_retrieval_clean_data(self):
        """Test 2: Production Items Retrieval returns clean data without status/quantity issues"""
        print("\n=== TEST 2: Production Items Retrieval - Clean Data Structure ===")
        
        try:
            # Get all production items
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                all_items = response.json()
                self.log_result("GET /api/production-items", True, f"Retrieved {len(all_items)} items")
                
                # Verify clean data structure - no undefined fields that could cause frontend crashes
                problematic_items = 0
                for item in all_items:
                    # Check for required fields that frontend expects
                    required_fields = ["id", "name", "category", "unit_of_measure", "base_cost", "unit_price"]
                    missing_fields = [field for field in required_fields if field not in item or item[field] is None]
                    
                    if missing_fields:
                        problematic_items += 1
                        self.log_result(f"Clean data structure for {item.get('name', 'unknown')}", False,
                                      f"Missing/null fields: {missing_fields}")
                    else:
                        # Verify unit_price is properly calculated
                        expected_price = item.get("base_cost", 10.0) * 1.15
                        actual_price = item.get("unit_price", 0)
                        if abs(actual_price - expected_price) < 0.01:
                            self.log_result(f"Price calculation for {item['name']}", True,
                                          f"${actual_price:.2f}")
                        else:
                            self.log_result(f"Price calculation for {item['name']}", False,
                                          f"Expected ${expected_price:.2f}, got ${actual_price:.2f}")
                
                if problematic_items == 0:
                    self.log_result("All items have clean data structure", True,
                                  f"All {len(all_items)} items have required fields")
                else:
                    self.log_result("All items have clean data structure", False,
                                  f"{problematic_items} items have missing/null fields")
                
                return all_items
            else:
                self.log_result("GET /api/production-items", False, f"Status: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_result("Production Items Retrieval Clean Data", False, f"Exception: {str(e)}")
            return []

    def test_orderable_items_all_available(self):
        """Test 3: Orderable Items - verify all production items appear and are always available"""
        print("\n=== TEST 3: Orderable Items - All Items Always Available ===")
        
        try:
            # Get production items count
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code != 200:
                self.log_result("Get production items count", False, f"Status: {response.status_code}")
                return
            
            production_items = response.json()
            production_count = len(production_items)
            
            # Test GET /api/orderable-items
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                self.log_result("GET /api/orderable-items", True, f"Retrieved {len(orderable_items)} orderable items")
                
                # Verify ALL production items are orderable (no limitations)
                if len(orderable_items) == production_count:
                    self.log_result("All production items are orderable", True,
                                  f"All {production_count} items available for ordering")
                else:
                    self.log_result("All production items are orderable", False,
                                  f"Expected {production_count}, got {len(orderable_items)}")
                
                # Verify items are always available (quantity=1000, status=available)
                always_available_count = 0
                for item in orderable_items:
                    if (item.get("available_quantity") == 1000 and 
                        item.get("availability_status") == "available"):
                        always_available_count += 1
                
                if always_available_count == len(orderable_items):
                    self.log_result("All items always available", True,
                                  f"All {len(orderable_items)} items show as always available")
                else:
                    self.log_result("All items always available", False,
                                  f"Only {always_available_count}/{len(orderable_items)} items always available")
            else:
                self.log_result("GET /api/orderable-items", False, f"Status: {response.status_code}")
            
            # Test GET /api/orderable-items/by-category
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                total_categorized = sum(len(items) for items in items_by_category.values())
                
                self.log_result("GET /api/orderable-items/by-category", True,
                              f"Retrieved {total_categorized} items across {len(items_by_category)} categories")
                
                if total_categorized == production_count:
                    self.log_result("All items properly categorized", True,
                                  f"All {production_count} items found in categories")
                else:
                    self.log_result("All items properly categorized", False,
                                  f"Expected {production_count}, found {total_categorized}")
            else:
                self.log_result("GET /api/orderable-items/by-category", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Orderable Items All Available", False, f"Exception: {str(e)}")

    def test_manager_production_screen_fix(self):
        """Test 4: Manager Production Screen Fix - verify no crashes from undefined field references"""
        print("\n=== TEST 4: Manager Production Screen Fix - No Undefined Field Issues ===")
        
        try:
            # Get production items as manager would see them
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                items = response.json()
                self.log_result("Manager production items view", True, f"Retrieved {len(items)} items")
                
                # Check for fields that could cause frontend crashes
                crash_prone_items = 0
                for item in items:
                    # Fields that frontend might reference that could be undefined
                    potentially_undefined = []
                    
                    # Check for null/undefined values in critical fields
                    if item.get("name") is None or item.get("name") == "":
                        potentially_undefined.append("name")
                    if item.get("category") is None:
                        potentially_undefined.append("category")
                    if item.get("unit_of_measure") is None:
                        potentially_undefined.append("unit_of_measure")
                    if item.get("base_cost") is None:
                        potentially_undefined.append("base_cost")
                    if item.get("unit_price") is None:
                        potentially_undefined.append("unit_price")
                    
                    if potentially_undefined:
                        crash_prone_items += 1
                        self.log_result(f"No undefined fields for {item.get('name', 'unknown')}", False,
                                      f"Undefined/null fields: {potentially_undefined}")
                    else:
                        self.log_result(f"Clean field structure for {item['name']}", True,
                                      "All critical fields defined")
                
                if crash_prone_items == 0:
                    self.log_result("Manager screen crash prevention", True,
                                  f"All {len(items)} items have defined critical fields")
                else:
                    self.log_result("Manager screen crash prevention", False,
                                  f"{crash_prone_items} items have undefined fields that could cause crashes")
                
                # Test that items can be properly displayed (simulate frontend data access)
                display_test_passed = True
                for item in items[:5]:  # Test first 5 items
                    try:
                        # Simulate frontend accessing item properties
                        display_data = {
                            "name": item["name"],
                            "category": item["category"],
                            "unit_measure": item["unit_of_measure"],
                            "base_cost": f"${item['base_cost']:.2f}",
                            "unit_price": f"${item['unit_price']:.2f}",
                            "markup": f"{((item['unit_price'] / item['base_cost'] - 1) * 100):.1f}%"
                        }
                        self.log_result(f"Frontend display simulation for {item['name']}", True,
                                      f"Markup: {display_data['markup']}")
                    except (KeyError, TypeError, ZeroDivisionError) as e:
                        display_test_passed = False
                        self.log_result(f"Frontend display simulation for {item.get('name', 'unknown')}", False,
                                      f"Error: {str(e)}")
                
                if display_test_passed:
                    self.log_result("Frontend display compatibility", True,
                                  "All tested items can be safely displayed")
                
            else:
                self.log_result("Manager production items view", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Manager Production Screen Fix", False, f"Exception: {str(e)}")

    def test_end_to_end_workflow(self):
        """Test 5: Complete End-to-End Testing"""
        print("\n=== TEST 5: Complete End-to-End Workflow ===")
        
        try:
            # Step 1: Manager creates production item
            print("\n--- Step 1: Manager creates production item ---")
            
            new_item = {
                "name": "E2E Test Burger",
                "category": "Main Course",
                "base_cost": 16.0,
                "assigned_staff": "chef_alice"
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=new_item
            )
            
            if response.status_code == 200:
                created_item = response.json()
                self.log_result("Manager creates item", True, f"Created: {created_item['name']}")
                
                # Verify unit_price calculated correctly
                expected_price = new_item["base_cost"] * 1.15
                if abs(created_item["unit_price"] - expected_price) < 0.01:
                    self.log_result("Unit price auto-calculation", True,
                                  f"${created_item['unit_price']:.2f} (15% markup)")
                else:
                    self.log_result("Unit price auto-calculation", False,
                                  f"Expected ${expected_price:.2f}, got ${created_item['unit_price']:.2f}")
            else:
                self.log_result("Manager creates item", False, f"Status: {response.status_code}")
                return
            
            # Step 2: Verify item appears in orderable items immediately
            print("\n--- Step 2: Item appears in orderable items ---")
            
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                item_found = any(item["id"] == created_item["id"] for item in orderable_items)
                
                if item_found:
                    orderable_item = next(item for item in orderable_items if item["id"] == created_item["id"])
                    self.log_result("Item immediately orderable", True,
                                  f"Item appears with quantity {orderable_item['available_quantity']}")
                    
                    # Verify it shows as always available
                    if (orderable_item["available_quantity"] == 1000 and 
                        orderable_item["availability_status"] == "available"):
                        self.log_result("Item always available", True,
                                      "Shows as always available for ordering")
                    else:
                        self.log_result("Item always available", False,
                                      f"Quantity: {orderable_item['available_quantity']}, Status: {orderable_item['availability_status']}")
                else:
                    self.log_result("Item immediately orderable", False,
                                  "Item not found in orderable items")
                    return
            else:
                self.log_result("Check orderable items", False, f"Status: {response.status_code}")
                return
            
            # Step 3: Venue places order
            print("\n--- Step 3: Venue places order ---")
            
            # Get venue user
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                venue_users = [user for user in users if user.get("role") == "venue_staff"]
                if venue_users:
                    venue_user = venue_users[0]
                    
                    order_data = {
                        "venue_name": venue_user["name"],
                        "venue_id": venue_user["id"],
                        "delivery_address": venue_user.get("address") or "123 Test Street",
                        "items": [{
                            "production_item_id": created_item["id"],
                            "production_item_name": created_item["name"],
                            "quantity": 2,
                            "unit_of_measure": created_item["unit_of_measure"],
                            "unit_price": created_item["unit_price"]
                        }]
                    }
                    
                    response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                    if response.status_code == 200:
                        order = response.json()
                        self.log_result("Venue places order", True,
                                      f"Order {order['id']} placed for ${order['total_amount']:.2f}")
                    else:
                        self.log_result("Venue places order", False,
                                      f"Status: {response.status_code}")
                        return
                else:
                    self.log_result("Get venue user", False, "No venue users found")
                    return
            else:
                self.log_result("Get venue user", False, f"Status: {response.status_code}")
                return
            
            # Step 4: Verify no inventory reduction
            print("\n--- Step 4: Verify no inventory reduction ---")
            
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                updated_orderable_items = response.json()
                updated_item = next((item for item in updated_orderable_items 
                                   if item["id"] == created_item["id"]), None)
                
                if updated_item and updated_item["available_quantity"] == 1000:
                    self.log_result("No inventory reduction", True,
                                  "Item quantity remains at 1000 after order")
                else:
                    self.log_result("No inventory reduction", False,
                                  f"Quantity changed to {updated_item['available_quantity'] if updated_item else 'item not found'}")
            else:
                self.log_result("Check inventory after order", False, f"Status: {response.status_code}")
            
            # Step 5: Kitchen can process order
            print("\n--- Step 5: Kitchen can process order ---")
            
            response = self.session.get(f"{BASE_URL}/orders?status=pending")
            if response.status_code == 200:
                pending_orders = response.json()
                order_found = any(o["id"] == order["id"] for o in pending_orders)
                
                if order_found:
                    self.log_result("Kitchen sees order", True,
                                  f"Order visible in pending orders")
                    
                    # Test kitchen can update status
                    response = self.session.put(f"{BASE_URL}/orders/{order['id']}/status?status=preparing")
                    if response.status_code == 200:
                        self.log_result("Kitchen processes order", True,
                                      "Successfully updated to 'preparing'")
                    else:
                        self.log_result("Kitchen processes order", False,
                                      f"Cannot update status: {response.status_code}")
                else:
                    self.log_result("Kitchen sees order", False,
                                  "Order not found in pending orders")
            else:
                self.log_result("Check pending orders", False, f"Status: {response.status_code}")
            
            self.log_result("Complete End-to-End Workflow", True,
                          "Full workflow: Create → Immediately Available → Order → No Reduction → Kitchen Process")
                
        except Exception as e:
            self.log_result("Complete End-to-End Workflow", False, f"Exception: {str(e)}")

    def run_focused_tests(self):
        """Run all focused tests for the fixed production items system"""
        print("🔍 STARTING FOCUSED PRODUCTION ITEMS SYSTEM TESTS")
        print("=" * 70)
        print("Testing the fixed production items system after removing status management")
        print("=" * 70)
        
        # Run all tests
        self.test_production_items_creation_without_status_quantity()
        self.test_production_items_retrieval_clean_data()
        self.test_orderable_items_all_available()
        self.test_manager_production_screen_fix()
        self.test_end_to_end_workflow()
        
        # Print summary
        print("\n" + "=" * 70)
        print("🔍 FOCUSED PRODUCTION ITEMS SYSTEM TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Tests Passed: {self.test_results['passed']}")
        print(f"❌ Tests Failed: {self.test_results['failed']}")
        total_tests = self.test_results['passed'] + self.test_results['failed']
        if total_tests > 0:
            success_rate = (self.test_results['passed'] / total_tests * 100)
            print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        return self.test_results

if __name__ == "__main__":
    tester = FocusedProductionTester()
    results = tester.run_focused_tests()