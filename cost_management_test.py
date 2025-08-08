#!/usr/bin/env python3
"""
Cost Management System Testing for Production Kitchen Management System
Focus: Testing new cost management system with automatic 15% markup calculation

Key Features to Test:
1. Production Item Creation with Base Cost - verify unit_price is automatically calculated as base_cost * 1.15
2. Cost Updates with Automatic Markup - test PUT /api/production-items/{id}/availability with base_cost updates
3. Manager-Only Pricing - verify base_cost is only accessible through manager endpoints
4. Complete Workflow - manager creates item, system calculates selling price, venue staff sees only selling price
5. Backward Compatibility - test existing items without base_cost work with defaults

Test Scenarios:
1. Create item with base_cost = $8.00, verify unit_price = $9.20
2. Update base_cost to $12.00, verify unit_price updates to $13.80
3. Test orderable items API returns correct selling prices
4. Verify orders are placed with the marked-up prices
5. Test that only managers can see/edit base costs
"""

import requests
import json
from datetime import datetime, date, timedelta
import time
import sys

# Backend URL from frontend/.env
BASE_URL = "https://523e0c6c-09ea-4970-8dcd-e42fec7deab4.preview.emergentagent.com/api"

class CostManagementTester:
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
    
    def test_production_item_creation_with_base_cost(self):
        """Test production item creation with base_cost and automatic unit_price calculation"""
        print("\n=== Testing Production Item Creation with Base Cost ===")
        
        try:
            # Test cases with different base costs
            test_items = [
                {
                    "name": "Cost Test Grilled Chicken",
                    "category": "Main Course",
                    "quantity": 20,
                    "unit_of_measure": "portions",
                    "base_cost": 8.00,
                    "expected_unit_price": 9.20  # 8.00 * 1.15
                },
                {
                    "name": "Cost Test Caesar Salad",
                    "category": "Salad",
                    "quantity": 15,
                    "unit_of_measure": "bowls",
                    "base_cost": 6.50,
                    "expected_unit_price": 7.475  # 6.50 * 1.15 = 7.475
                },
                {
                    "name": "Cost Test Chocolate Cake",
                    "category": "Dessert",
                    "quantity": 12,
                    "unit_of_measure": "slices",
                    "base_cost": 4.00,
                    "expected_unit_price": 4.60  # 4.00 * 1.15
                }
            ]
            
            created_items = []
            
            for item_data in test_items:
                expected_price = item_data.pop("expected_unit_price")
                
                response = self.session.post(
                    f"{BASE_URL}/production-items?created_by=manager",
                    json=item_data
                )
                
                if response.status_code == 200:
                    item = response.json()
                    created_items.append(item)
                    
                    # Verify base_cost is stored correctly
                    if abs(item.get("base_cost", 0) - item_data["base_cost"]) < 0.01:
                        self.log_result(f"Base cost storage for {item_data['name']}", True,
                                      f"Base cost: ${item['base_cost']}")
                    else:
                        self.log_result(f"Base cost storage for {item_data['name']}", False,
                                      f"Expected ${item_data['base_cost']}, got ${item.get('base_cost', 0)}")
                    
                    # Verify unit_price is automatically calculated with 15% markup
                    actual_price = item.get("unit_price", 0)
                    if abs(actual_price - expected_price) < 0.01:
                        self.log_result(f"Automatic 15% markup for {item_data['name']}", True,
                                      f"Base: ${item_data['base_cost']} → Selling: ${actual_price}")
                    else:
                        self.log_result(f"Automatic 15% markup for {item_data['name']}", False,
                                      f"Expected ${expected_price}, got ${actual_price}")
                    
                    # Verify both base_cost and unit_price are stored
                    if "base_cost" in item and "unit_price" in item:
                        self.log_result(f"Cost fields storage for {item_data['name']}", True,
                                      "Both base_cost and unit_price stored")
                    else:
                        missing = []
                        if "base_cost" not in item:
                            missing.append("base_cost")
                        if "unit_price" not in item:
                            missing.append("unit_price")
                        self.log_result(f"Cost fields storage for {item_data['name']}", False,
                                      f"Missing fields: {missing}")
                    
                    self.log_result(f"Create item with base cost: {item_data['name']}", True,
                                  f"ID: {item['id']}")
                else:
                    self.log_result(f"Create item with base cost: {item_data['name']}", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            return created_items
            
        except Exception as e:
            self.log_result("Production Item Creation with Base Cost", False, f"Exception: {str(e)}")
            return []
    
    def test_cost_updates_with_automatic_markup(self, created_items):
        """Test PUT /api/production-items/{id}/availability with base_cost updates"""
        print("\n=== Testing Cost Updates with Automatic Markup ===")
        
        try:
            if not created_items:
                self.log_result("Cost Updates with Automatic Markup", False, "No items to test with")
                return []
            
            updated_items = []
            
            # Test different base_cost update scenarios
            update_scenarios = [
                {
                    "base_cost": 12.00,
                    "expected_unit_price": 13.80  # 12.00 * 1.15
                },
                {
                    "base_cost": 15.50,
                    "expected_unit_price": 17.825  # 15.50 * 1.15
                },
                {
                    "base_cost": 9.25,
                    "expected_unit_price": 10.6375  # 9.25 * 1.15
                }
            ]
            
            for i, item in enumerate(created_items[:3]):  # Test first 3 items
                if i >= len(update_scenarios):
                    break
                    
                item_id = item["id"]
                item_name = item["name"]
                scenario = update_scenarios[i]
                
                # Update base_cost via availability endpoint
                update_data = {
                    "base_cost": scenario["base_cost"],
                    "available_for_order": 10,
                    "availability_status": "available"
                }
                
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item_id}/availability",
                    json=update_data
                )
                
                if response.status_code == 200:
                    self.log_result(f"Update base cost for {item_name}", True,
                                  f"New base cost: ${scenario['base_cost']}")
                    
                    # Verify the update by fetching the item
                    response = self.session.get(f"{BASE_URL}/production-items")
                    if response.status_code == 200:
                        all_items = response.json()
                        updated_item = next((item for item in all_items if item["id"] == item_id), None)
                        
                        if updated_item:
                            # Verify base_cost was updated
                            actual_base_cost = updated_item.get("base_cost", 0)
                            if abs(actual_base_cost - scenario["base_cost"]) < 0.01:
                                self.log_result(f"Base cost update verification for {item_name}", True,
                                              f"Base cost: ${actual_base_cost}")
                            else:
                                self.log_result(f"Base cost update verification for {item_name}", False,
                                              f"Expected ${scenario['base_cost']}, got ${actual_base_cost}")
                            
                            # Verify unit_price was automatically recalculated
                            actual_unit_price = updated_item.get("unit_price", 0)
                            expected_unit_price = scenario["expected_unit_price"]
                            if abs(actual_unit_price - expected_unit_price) < 0.01:
                                self.log_result(f"Automatic markup recalculation for {item_name}", True,
                                              f"${scenario['base_cost']} → ${actual_unit_price} (15% markup)")
                            else:
                                self.log_result(f"Automatic markup recalculation for {item_name}", False,
                                              f"Expected ${expected_unit_price}, got ${actual_unit_price}")
                            
                            # Verify markup calculation is accurate (15%)
                            if actual_base_cost > 0:
                                calculated_markup = ((actual_unit_price - actual_base_cost) / actual_base_cost) * 100
                                if abs(calculated_markup - 15.0) < 0.1:
                                    self.log_result(f"15% markup accuracy for {item_name}", True,
                                                  f"Markup: {calculated_markup:.1f}%")
                                else:
                                    self.log_result(f"15% markup accuracy for {item_name}", False,
                                                  f"Expected 15%, got {calculated_markup:.1f}%")
                            
                            updated_items.append(updated_item)
                        else:
                            self.log_result(f"Fetch updated item {item_name}", False, "Item not found after update")
                    else:
                        self.log_result(f"Fetch updated item {item_name}", False, f"Status: {response.status_code}")
                else:
                    self.log_result(f"Update base cost for {item_name}", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            return updated_items
            
        except Exception as e:
            self.log_result("Cost Updates with Automatic Markup", False, f"Exception: {str(e)}")
            return []
    
    def test_manager_only_pricing_access(self, updated_items):
        """Test that base_cost information is only accessible through manager endpoints"""
        print("\n=== Testing Manager-Only Pricing Access ===")
        
        try:
            if not updated_items:
                self.log_result("Manager-Only Pricing Access", False, "No items to test with")
                return
            
            # Test that production items endpoint (manager access) shows base_cost
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                production_items = response.json()
                test_item = next((item for item in production_items if item["id"] == updated_items[0]["id"]), None)
                
                if test_item:
                    if "base_cost" in test_item:
                        self.log_result("Manager endpoint shows base_cost", True,
                                      f"Base cost visible: ${test_item['base_cost']}")
                    else:
                        self.log_result("Manager endpoint shows base_cost", False,
                                      "base_cost field missing from manager endpoint")
                    
                    if "unit_price" in test_item:
                        self.log_result("Manager endpoint shows unit_price", True,
                                      f"Unit price visible: ${test_item['unit_price']}")
                    else:
                        self.log_result("Manager endpoint shows unit_price", False,
                                      "unit_price field missing from manager endpoint")
                else:
                    self.log_result("Manager endpoint access", False, "Test item not found")
            else:
                self.log_result("Manager endpoint access", False, f"Status: {response.status_code}")
            
            # Test that orderable items endpoint (venue staff access) only shows unit_price
            # First mark items as completed so they appear in orderable items
            for item in updated_items[:2]:
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item['id']}/status?status=completed"
                )
                if response.status_code == 200:
                    self.log_result(f"Mark {item['name']} as completed for orderable test", True, "Status updated")
                else:
                    self.log_result(f"Mark {item['name']} as completed for orderable test", False, f"Status: {response.status_code}")
            
            # Test orderable items endpoint (venue staff view)
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                test_orderable = next((item for item in orderable_items if item["id"] == updated_items[0]["id"]), None)
                
                if test_orderable:
                    # Venue staff should see unit_price (selling price)
                    if "unit_price" in test_orderable:
                        self.log_result("Venue staff sees selling price", True,
                                      f"Unit price visible: ${test_orderable['unit_price']}")
                    else:
                        self.log_result("Venue staff sees selling price", False,
                                      "unit_price missing from venue staff view")
                    
                    # Venue staff should NOT see base_cost
                    if "base_cost" not in test_orderable:
                        self.log_result("Base cost hidden from venue staff", True,
                                      "base_cost field properly hidden")
                    else:
                        self.log_result("Base cost hidden from venue staff", False,
                                      f"base_cost exposed: ${test_orderable['base_cost']}")
                else:
                    self.log_result("Venue staff orderable items access", False, "Test item not found in orderable items")
            else:
                self.log_result("Venue staff orderable items access", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Manager-Only Pricing Access", False, f"Exception: {str(e)}")
    
    def test_complete_cost_management_workflow(self):
        """Test the complete cost management workflow"""
        print("\n=== Testing Complete Cost Management Workflow ===")
        
        try:
            # Step 1: Manager creates item with base cost (e.g., $10.00)
            workflow_item = {
                "name": "Workflow Premium Steak",
                "category": "Main Course",
                "quantity": 15,
                "unit_of_measure": "steaks",
                "base_cost": 10.00
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=workflow_item
            )
            
            if response.status_code == 200:
                created_item = response.json()
                
                # Step 2: System calculates selling price ($11.50 with 15% markup)
                expected_selling_price = 11.50  # 10.00 * 1.15
                actual_selling_price = created_item.get("unit_price", 0)
                
                if abs(actual_selling_price - expected_selling_price) < 0.01:
                    self.log_result("Step 1-2: Manager creates item, system calculates selling price", True,
                                  f"Base: ${workflow_item['base_cost']} → Selling: ${actual_selling_price}")
                else:
                    self.log_result("Step 1-2: Manager creates item, system calculates selling price", False,
                                  f"Expected ${expected_selling_price}, got ${actual_selling_price}")
                
                # Step 3: Set availability and mark as completed
                availability_data = {
                    "available_for_order": 10,
                    "availability_status": "available"
                }
                
                response = self.session.put(
                    f"{BASE_URL}/production-items/{created_item['id']}/availability",
                    json=availability_data
                )
                
                if response.status_code == 200:
                    # Mark as completed
                    response = self.session.put(
                        f"{BASE_URL}/production-items/{created_item['id']}/status?status=completed"
                    )
                    
                    if response.status_code == 200:
                        self.log_result("Step 3: Set availability and mark completed", True,
                                      "Item ready for ordering")
                        
                        # Step 4: Venue staff sees only the selling price in ordering interface
                        response = self.session.get(f"{BASE_URL}/orderable-items")
                        if response.status_code == 200:
                            orderable_items = response.json()
                            workflow_orderable = next((item for item in orderable_items 
                                                     if item["id"] == created_item["id"]), None)
                            
                            if workflow_orderable:
                                # Verify venue staff sees selling price but not base cost
                                if ("unit_price" in workflow_orderable and 
                                    "base_cost" not in workflow_orderable and
                                    abs(workflow_orderable["unit_price"] - expected_selling_price) < 0.01):
                                    self.log_result("Step 4: Venue staff sees only selling price", True,
                                                  f"Selling price: ${workflow_orderable['unit_price']}, base cost hidden")
                                else:
                                    issues = []
                                    if "unit_price" not in workflow_orderable:
                                        issues.append("unit_price missing")
                                    if "base_cost" in workflow_orderable:
                                        issues.append("base_cost exposed")
                                    if abs(workflow_orderable.get("unit_price", 0) - expected_selling_price) >= 0.01:
                                        issues.append("incorrect selling price")
                                    self.log_result("Step 4: Venue staff sees only selling price", False,
                                                  f"Issues: {', '.join(issues)}")
                            else:
                                self.log_result("Step 4: Venue staff sees only selling price", False,
                                              "Item not found in orderable items")
                        else:
                            self.log_result("Step 4: Venue staff sees only selling price", False,
                                          f"Orderable items API failed: {response.status_code}")
                        
                        # Step 5: Orders are processed with the marked-up price
                        # Get venue user for order
                        response = self.session.get(f"{BASE_URL}/users")
                        if response.status_code == 200:
                            users = response.json()
                            venue_user = next((user for user in users if user.get("role") == "venue_staff"), None)
                            
                            if venue_user and workflow_orderable:
                                order_items = [
                                    {
                                        "production_item_id": created_item["id"],
                                        "production_item_name": created_item["name"],
                                        "quantity": 2,
                                        "unit_of_measure": created_item["unit_of_measure"],
                                        "unit_price": workflow_orderable["unit_price"]  # Using marked-up price
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
                                    
                                    # Verify order uses marked-up price
                                    order_item = order["items"][0]
                                    if abs(order_item["unit_price"] - expected_selling_price) < 0.01:
                                        self.log_result("Step 5: Orders processed with marked-up price", True,
                                                      f"Order uses selling price: ${order_item['unit_price']}")
                                        
                                        # Verify order total calculation
                                        expected_subtotal = 2 * expected_selling_price  # 2 steaks * $11.50
                                        if abs(order["subtotal"] - expected_subtotal) < 0.01:
                                            self.log_result("Step 5: Order total calculation with markup", True,
                                                          f"Subtotal: ${order['subtotal']} (2 × ${expected_selling_price})")
                                        else:
                                            self.log_result("Step 5: Order total calculation with markup", False,
                                                          f"Expected ${expected_subtotal}, got ${order['subtotal']}")
                                    else:
                                        self.log_result("Step 5: Orders processed with marked-up price", False,
                                                      f"Expected ${expected_selling_price}, got ${order_item['unit_price']}")
                                else:
                                    self.log_result("Step 5: Orders processed with marked-up price", False,
                                                  f"Order creation failed: {response.status_code}")
                            else:
                                self.log_result("Step 5: Orders processed with marked-up price", False,
                                              "No venue user or orderable item available")
                        else:
                            self.log_result("Step 5: Orders processed with marked-up price", False,
                                          f"Users API failed: {response.status_code}")
                    else:
                        self.log_result("Step 3: Mark as completed", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Step 3: Set availability", False, f"Status: {response.status_code}")
            else:
                self.log_result("Step 1: Manager creates item with base cost", False,
                              f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Complete Cost Management Workflow", False, f"Exception: {str(e)}")
    
    def test_backward_compatibility(self):
        """Test that existing items without base_cost work with default values"""
        print("\n=== Testing Backward Compatibility ===")
        
        try:
            # Create item without base_cost (should use default)
            legacy_item = {
                "name": "Legacy Menu Item",
                "category": "Main Course",
                "quantity": 10,
                "unit_of_measure": "portions"
                # No base_cost specified
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=legacy_item
            )
            
            if response.status_code == 200:
                item = response.json()
                
                # Verify default base_cost is applied
                default_base_cost = 10.0  # From ProductionItem model
                if abs(item.get("base_cost", 0) - default_base_cost) < 0.01:
                    self.log_result("Default base_cost for legacy item", True,
                                  f"Default base cost: ${item['base_cost']}")
                else:
                    self.log_result("Default base_cost for legacy item", False,
                                  f"Expected ${default_base_cost}, got ${item.get('base_cost', 0)}")
                
                # Verify default unit_price calculation
                expected_unit_price = 11.5  # 10.0 * 1.15
                if abs(item.get("unit_price", 0) - expected_unit_price) < 0.01:
                    self.log_result("Default unit_price calculation for legacy item", True,
                                  f"Default unit price: ${item['unit_price']}")
                else:
                    self.log_result("Default unit_price calculation for legacy item", False,
                                  f"Expected ${expected_unit_price}, got ${item.get('unit_price', 0)}")
                
                # Test that legacy item can be updated with new base_cost
                update_data = {
                    "base_cost": 8.50,
                    "available_for_order": 5
                }
                
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item['id']}/availability",
                    json=update_data
                )
                
                if response.status_code == 200:
                    # Verify update worked
                    response = self.session.get(f"{BASE_URL}/production-items")
                    if response.status_code == 200:
                        all_items = response.json()
                        updated_item = next((i for i in all_items if i["id"] == item["id"]), None)
                        
                        if updated_item:
                            expected_new_price = 9.775  # 8.50 * 1.15
                            if (abs(updated_item.get("base_cost", 0) - 8.50) < 0.01 and
                                abs(updated_item.get("unit_price", 0) - expected_new_price) < 0.01):
                                self.log_result("Legacy item cost update", True,
                                              f"Updated: ${8.50} → ${updated_item['unit_price']}")
                            else:
                                self.log_result("Legacy item cost update", False,
                                              f"Base: {updated_item.get('base_cost')}, Price: {updated_item.get('unit_price')}")
                        else:
                            self.log_result("Legacy item cost update", False, "Updated item not found")
                    else:
                        self.log_result("Legacy item cost update", False, "Cannot fetch updated item")
                else:
                    self.log_result("Legacy item cost update", False, f"Update failed: {response.status_code}")
                
                self.log_result("Create legacy item without base_cost", True, f"ID: {item['id']}")
            else:
                self.log_result("Create legacy item without base_cost", False,
                              f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Backward Compatibility", False, f"Exception: {str(e)}")
    
    def run_cost_management_tests(self):
        """Run comprehensive tests for the cost management system"""
        print("🧪 Starting Cost Management System Backend API Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Focus: New cost management system with automatic 15% markup calculation")
        print("=" * 80)
        
        # Test 1: Production Item Creation with Base Cost
        created_items = self.test_production_item_creation_with_base_cost()
        
        # Test 2: Cost Updates with Automatic Markup
        updated_items = self.test_cost_updates_with_automatic_markup(created_items)
        
        # Test 3: Manager-Only Pricing Access
        self.test_manager_only_pricing_access(updated_items)
        
        # Test 4: Complete Cost Management Workflow
        self.test_complete_cost_management_workflow()
        
        # Test 5: Backward Compatibility
        self.test_backward_compatibility()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 COST MANAGEMENT SYSTEM TEST SUMMARY")
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
    tester = CostManagementTester()
    success = tester.run_cost_management_tests()
    sys.exit(0 if success else 1)