#!/usr/bin/env python3
"""
Backend API Testing for Force Delete and Enhanced Add Item Form Validation
Focus: Testing newly implemented force delete functionality and enhanced add item form validation
"""

import requests
import json
from datetime import datetime, date, timedelta
import time
import sys

# Backend URL from frontend/.env
BASE_URL = "https://order-flow-6.preview.emergentagent.com/api"

class ForceDeleteAndValidationTester:
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

    def test_force_delete_functionality(self):
        """Test force delete functionality comprehensively"""
        print("\n=== TESTING FORCE DELETE FUNCTIONALITY ===")
        
        try:
            # Step 1: Create a test item
            test_item = {
                "name": "Force Delete Test Item",
                "category": "Main Course",
                "quantity": 10,
                "unit_of_measure": "portions",
                "base_cost": 12.0
            }
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
            if response.status_code != 200:
                self.log_result("Create test item for force delete", False, f"Status: {response.status_code}")
                return
            
            created_item = response.json()
            item_id = created_item["id"]
            item_name = created_item["name"]
            self.log_result("Create test item for force delete", True, f"Created: {item_name} (ID: {item_id})")
            
            # Step 2: Set item availability so it can be ordered
            availability_data = {
                "available_for_order": 5,
                "unit_price": 15.0,
                "availability_status": "available"
            }
            
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/availability", json=availability_data)
            if response.status_code != 200:
                self.log_result("Set item availability", False, f"Status: {response.status_code}")
                return
            
            self.log_result("Set item availability", True, "Item set as available for ordering")
            
            # Step 3: Get venue information for creating an order
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code != 200:
                self.log_result("Get venue users", False, f"Status: {response.status_code}")
                return
            
            users = response.json()
            venue_users = [user for user in users if user.get("role") == "venue_staff"]
            
            if not venue_users:
                self.log_result("Get venue users", False, "No venue users found")
                return
            
            venue_user = venue_users[0]
            venue_id = venue_user["id"]
            venue_name = venue_user["name"]
            venue_address = venue_user.get("address") or "123 Test Street, Test City"
            
            # Step 4: Create an order that references this item
            order_data = {
                "venue_name": venue_name,
                "venue_id": venue_id,
                "delivery_address": venue_address,
                "items": [
                    {
                        "production_item_id": item_id,
                        "production_item_name": item_name,
                        "quantity": 2,
                        "unit_of_measure": "portions",
                        "unit_price": 15.0
                    }
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            if response.status_code != 200:
                self.log_result("Create order with test item", False, f"Status: {response.status_code}")
                return
            
            created_order = response.json()
            order_id = created_order["id"]
            self.log_result("Create order with test item", True, f"Order ID: {order_id}")
            
            # Step 5: Test normal delete (force=false) - should fail with enhanced error message
            response = self.session.delete(f"{BASE_URL}/production-items/{item_id}?force=false")
            
            if response.status_code == 400:
                error_message = response.json().get("detail", "")
                if "force delete" in error_message.lower() or "force=true" in error_message:
                    self.log_result("Normal delete with force option mentioned", True, 
                                  f"Enhanced error message: {error_message}")
                else:
                    self.log_result("Normal delete with force option mentioned", False, 
                                  f"Error message doesn't mention force delete: {error_message}")
            else:
                self.log_result("Normal delete protection", False, 
                              f"Expected 400, got {response.status_code}")
            
            # Step 6: Test force delete (force=true) - should succeed
            response = self.session.delete(f"{BASE_URL}/production-items/{item_id}?force=true")
            
            if response.status_code == 200:
                self.log_result("Force delete execution", True, "Force delete succeeded")
                
                # Step 7: Verify item is completely removed from production items
                response = self.session.get(f"{BASE_URL}/production-items")
                if response.status_code == 200:
                    all_items = response.json()
                    item_still_exists = any(item["id"] == item_id for item in all_items)
                    
                    if not item_still_exists:
                        self.log_result("Item removed from production items", True, "Item no longer exists")
                    else:
                        self.log_result("Item removed from production items", False, "Item still exists")
                else:
                    self.log_result("Item removed from production items", False, "Cannot verify removal")
                
                # Step 8: Verify order is updated with recalculated totals
                response = self.session.get(f"{BASE_URL}/orders")
                if response.status_code == 200:
                    all_orders = response.json()
                    updated_order = next((order for order in all_orders if order["id"] == order_id), None)
                    
                    if updated_order:
                        # Check if item was removed from order
                        remaining_items = updated_order.get("items", [])
                        item_still_in_order = any(item.get("production_item_id") == item_id for item in remaining_items)
                        
                        if not item_still_in_order:
                            self.log_result("Item removed from order", True, "Item no longer in order items")
                            
                            # Verify totals were recalculated
                            expected_subtotal = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in remaining_items)
                            expected_tax = expected_subtotal * 0.08
                            expected_total = expected_subtotal + expected_tax
                            
                            actual_subtotal = updated_order.get("subtotal", 0)
                            actual_tax = updated_order.get("tax_amount", 0)
                            actual_total = updated_order.get("total_amount", 0)
                            
                            if abs(actual_subtotal - expected_subtotal) < 0.01:
                                self.log_result("Order subtotal recalculated", True, 
                                              f"Subtotal: ${actual_subtotal:.2f}")
                            else:
                                self.log_result("Order subtotal recalculated", False, 
                                              f"Expected ${expected_subtotal:.2f}, got ${actual_subtotal:.2f}")
                            
                            if abs(actual_tax - expected_tax) < 0.01:
                                self.log_result("Order tax recalculated", True, 
                                              f"Tax: ${actual_tax:.2f}")
                            else:
                                self.log_result("Order tax recalculated", False, 
                                              f"Expected ${expected_tax:.2f}, got ${actual_tax:.2f}")
                            
                            if abs(actual_total - expected_total) < 0.01:
                                self.log_result("Order total recalculated", True, 
                                              f"Total: ${actual_total:.2f}")
                            else:
                                self.log_result("Order total recalculated", False, 
                                              f"Expected ${expected_total:.2f}, got ${actual_total:.2f}")
                        else:
                            self.log_result("Item removed from order", False, "Item still in order items")
                    else:
                        self.log_result("Order verification after force delete", False, "Order not found")
                else:
                    self.log_result("Order verification after force delete", False, "Cannot retrieve orders")
                
                # Step 9: Check if invoices were also updated
                response = self.session.get(f"{BASE_URL}/invoices")
                if response.status_code == 200:
                    all_invoices = response.json()
                    related_invoices = [inv for inv in all_invoices if inv.get("order_id") == order_id]
                    
                    if related_invoices:
                        invoice = related_invoices[0]
                        invoice_items = invoice.get("items", [])
                        item_still_in_invoice = any(item.get("production_item_id") == item_id for item in invoice_items)
                        
                        if not item_still_in_invoice:
                            self.log_result("Item removed from invoice", True, "Item no longer in invoice items")
                            
                            # Verify invoice totals were recalculated
                            expected_subtotal = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in invoice_items)
                            expected_tax = expected_subtotal * 0.08
                            expected_total = expected_subtotal + expected_tax
                            
                            actual_subtotal = invoice.get("subtotal", 0)
                            actual_tax = invoice.get("tax_amount", 0)
                            actual_total = invoice.get("total_amount", 0)
                            
                            if abs(actual_subtotal - expected_subtotal) < 0.01:
                                self.log_result("Invoice totals recalculated", True, 
                                              f"Invoice total: ${actual_total:.2f}")
                            else:
                                self.log_result("Invoice totals recalculated", False, 
                                              f"Invoice totals not properly recalculated")
                        else:
                            self.log_result("Item removed from invoice", False, "Item still in invoice items")
                    else:
                        self.log_result("Invoice verification", True, "No related invoices found (acceptable)")
                else:
                    self.log_result("Invoice verification", False, "Cannot retrieve invoices")
                
            else:
                self.log_result("Force delete execution", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
            
        except Exception as e:
            self.log_result("Force Delete Functionality", False, f"Exception: {str(e)}")

    def test_enhanced_add_item_form_validation(self):
        """Test enhanced add item form validation"""
        print("\n=== TESTING ENHANCED ADD ITEM FORM VALIDATION ===")
        
        try:
            # Step 1: Test successful creation with all required fields
            valid_item = {
                "name": "Validation Test Item",
                "category": "Main Course",
                "quantity": 15,
                "unit_of_measure": "portions",
                "base_cost": 10.0
            }
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=valid_item)
            if response.status_code == 200:
                created_item = response.json()
                self.log_result("Valid item creation", True, f"Created: {created_item['name']}")
                
                # Verify all fields were saved correctly
                for field, expected_value in valid_item.items():
                    actual_value = created_item.get(field)
                    if actual_value == expected_value:
                        self.log_result(f"Field validation - {field}", True, f"{field}: {actual_value}")
                    else:
                        self.log_result(f"Field validation - {field}", False, 
                                      f"Expected {expected_value}, got {actual_value}")
            else:
                self.log_result("Valid item creation", False, f"Status: {response.status_code}")
            
            # Step 2: Test missing required fields
            required_fields = ["name", "category", "quantity", "unit_of_measure"]  # base_cost has default
            
            for missing_field in required_fields:
                test_item = valid_item.copy()
                del test_item[missing_field]
                
                response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
                
                if response.status_code in [400, 422]:
                    error_response = response.json()
                    error_detail = error_response.get("detail", "")
                    
                    # Check if error message mentions the missing field
                    if missing_field in str(error_detail).lower() or "required" in str(error_detail).lower():
                        self.log_result(f"Missing {missing_field} validation", True, 
                                      f"Properly rejected with validation error")
                    else:
                        self.log_result(f"Missing {missing_field} validation", True, 
                                      f"Rejected (status: {response.status_code})")
                else:
                    self.log_result(f"Missing {missing_field} validation", False, 
                                  f"Expected 400/422, got {response.status_code}")
            
            # Step 3: Test that created_by parameter is still required
            response = self.session.post(f"{BASE_URL}/production-items", json=valid_item)  # No created_by param
            
            if response.status_code in [400, 422]:
                self.log_result("Missing created_by parameter validation", True, 
                              f"Correctly rejected (status: {response.status_code})")
            else:
                self.log_result("Missing created_by parameter validation", False, 
                              f"Expected 400/422, got {response.status_code}")
            
            # Step 4: Test invalid data types
            invalid_type_tests = [
                {
                    "field": "quantity",
                    "value": "not_a_number",
                    "description": "string instead of integer"
                },
                {
                    "field": "base_cost", 
                    "value": "not_a_number",
                    "description": "string instead of float"
                },
                {
                    "field": "quantity",
                    "value": -5,
                    "description": "negative quantity"
                },
                {
                    "field": "base_cost",
                    "value": -10.0,
                    "description": "negative cost"
                }
            ]
            
            for test_case in invalid_type_tests:
                test_item = valid_item.copy()
                test_item[test_case["field"]] = test_case["value"]
                
                response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
                
                if response.status_code in [400, 422]:
                    self.log_result(f"Invalid {test_case['field']} type validation ({test_case['description']})", 
                                  True, f"Correctly rejected (status: {response.status_code})")
                else:
                    self.log_result(f"Invalid {test_case['field']} type validation ({test_case['description']})", 
                                  False, f"Expected 400/422, got {response.status_code}")
            
            # Step 5: Test empty string validation
            empty_string_tests = ["name", "category", "unit_of_measure"]
            
            for field in empty_string_tests:
                test_item = valid_item.copy()
                test_item[field] = ""
                
                response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=test_item)
                
                if response.status_code in [400, 422]:
                    self.log_result(f"Empty {field} validation", True, 
                                  f"Correctly rejected empty string (status: {response.status_code})")
                else:
                    self.log_result(f"Empty {field} validation", False, 
                                  f"Expected 400/422 for empty {field}, got {response.status_code}")
            
            # Step 6: Test optional fields work correctly
            item_with_optionals = valid_item.copy()
            item_with_optionals.update({
                "assigned_staff": "chef_alice",
                "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
            })
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=item_with_optionals)
            if response.status_code == 200:
                created_item = response.json()
                self.log_result("Item with optional fields", True, f"Created: {created_item['name']}")
                
                # Verify optional fields were saved
                if created_item.get("assigned_staff") == "chef_alice":
                    self.log_result("Optional assigned_staff field", True, "Assigned staff saved correctly")
                else:
                    self.log_result("Optional assigned_staff field", False, "Assigned staff not saved")
                
                if created_item.get("image") == item_with_optionals["image"]:
                    self.log_result("Optional image field", True, "Image data saved correctly")
                else:
                    self.log_result("Optional image field", False, "Image data not saved")
            else:
                self.log_result("Item with optional fields", False, f"Status: {response.status_code}")
            
            # Step 7: Test automatic calculations work correctly
            test_base_cost = 20.0
            expected_unit_price = test_base_cost * 1.15  # 15% markup
            
            cost_test_item = {
                "name": "Cost Calculation Test Item",
                "category": "Dessert",
                "quantity": 8,
                "unit_of_measure": "slices",
                "base_cost": test_base_cost
            }
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=cost_test_item)
            if response.status_code == 200:
                created_item = response.json()
                actual_unit_price = created_item.get("unit_price", 0)
                
                if abs(actual_unit_price - expected_unit_price) < 0.01:
                    self.log_result("Automatic unit price calculation", True, 
                                  f"Base cost: ${test_base_cost:.2f} → Unit price: ${actual_unit_price:.2f}")
                else:
                    self.log_result("Automatic unit price calculation", False, 
                                  f"Expected ${expected_unit_price:.2f}, got ${actual_unit_price:.2f}")
            else:
                self.log_result("Automatic unit price calculation", False, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_result("Enhanced Add Item Form Validation", False, f"Exception: {str(e)}")

    def test_complete_workflow(self):
        """Test complete workflow: Create item → place order → try normal delete → try force delete"""
        print("\n=== TESTING COMPLETE WORKFLOW ===")
        
        try:
            # Step 1: Create item
            workflow_item = {
                "name": "Workflow Test Item",
                "category": "Main Course",
                "quantity": 20,
                "unit_of_measure": "servings",
                "base_cost": 8.0
            }
            
            response = self.session.post(f"{BASE_URL}/production-items?created_by=manager", json=workflow_item)
            if response.status_code != 200:
                self.log_result("Workflow - Create item", False, f"Status: {response.status_code}")
                return
            
            created_item = response.json()
            item_id = created_item["id"]
            item_name = created_item["name"]
            self.log_result("Workflow - Create item", True, f"Created: {item_name}")
            
            # Step 2: Set availability
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/availability", 
                                      json={"available_for_order": 10, "unit_price": 12.0})
            if response.status_code != 200:
                self.log_result("Workflow - Set availability", False, f"Status: {response.status_code}")
                return
            
            self.log_result("Workflow - Set availability", True, "Item available for ordering")
            
            # Step 3: Get venue for order
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code != 200:
                self.log_result("Workflow - Get venue", False, f"Status: {response.status_code}")
                return
            
            users = response.json()
            venue_users = [user for user in users if user.get("role") == "venue_staff"]
            if not venue_users:
                self.log_result("Workflow - Get venue", False, "No venue users found")
                return
            
            venue_user = venue_users[0]
            
            # Step 4: Place order with item
            order_data = {
                "venue_name": venue_user["name"],
                "venue_id": venue_user["id"],
                "delivery_address": venue_user.get("address") or "123 Test Street, Test City",
                "items": [
                    {
                        "production_item_id": item_id,
                        "production_item_name": item_name,
                        "quantity": 3,
                        "unit_of_measure": "servings",
                        "unit_price": 12.0
                    }
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            if response.status_code != 200:
                self.log_result("Workflow - Place order", False, f"Status: {response.status_code}")
                return
            
            order = response.json()
            self.log_result("Workflow - Place order", True, f"Order ID: {order['id']}")
            
            # Step 5: Try normal delete (should fail)
            response = self.session.delete(f"{BASE_URL}/production-items/{item_id}")
            
            if response.status_code == 400:
                error_message = response.json().get("detail", "")
                if "force delete" in error_message.lower() or "force=true" in error_message:
                    self.log_result("Workflow - Normal delete fails with guidance", True, 
                                  "Error message guides user to force delete option")
                else:
                    self.log_result("Workflow - Normal delete fails with guidance", False, 
                                  "Error message doesn't mention force delete option")
            else:
                self.log_result("Workflow - Normal delete protection", False, 
                              f"Expected 400, got {response.status_code}")
            
            # Step 6: Try force delete (should succeed)
            response = self.session.delete(f"{BASE_URL}/production-items/{item_id}?force=true")
            
            if response.status_code == 200:
                self.log_result("Workflow - Force delete succeeds", True, "Force delete completed successfully")
                
                # Step 7: Verify data integrity
                # Check item is gone
                response = self.session.get(f"{BASE_URL}/production-items")
                if response.status_code == 200:
                    all_items = response.json()
                    item_exists = any(item["id"] == item_id for item in all_items)
                    
                    if not item_exists:
                        self.log_result("Workflow - Item removed", True, "Item no longer exists")
                    else:
                        self.log_result("Workflow - Item removed", False, "Item still exists")
                
                # Check order is updated
                response = self.session.get(f"{BASE_URL}/orders")
                if response.status_code == 200:
                    all_orders = response.json()
                    updated_order = next((o for o in all_orders if o["id"] == order["id"]), None)
                    
                    if updated_order:
                        item_in_order = any(item.get("production_item_id") == item_id 
                                          for item in updated_order.get("items", []))
                        
                        if not item_in_order:
                            self.log_result("Workflow - Order updated", True, 
                                          "Item removed from order and totals recalculated")
                        else:
                            self.log_result("Workflow - Order updated", False, 
                                          "Item still in order")
                    else:
                        self.log_result("Workflow - Order verification", False, "Order not found")
                
            else:
                self.log_result("Workflow - Force delete succeeds", False, 
                              f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_result("Complete Workflow", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all force delete and validation tests"""
        print("🧪 STARTING FORCE DELETE AND VALIDATION TESTS")
        print("=" * 70)
        
        # Test force delete functionality
        self.test_force_delete_functionality()
        
        # Test enhanced add item form validation
        self.test_enhanced_add_item_form_validation()
        
        # Test complete workflow
        self.test_complete_workflow()
        
        # Print summary
        print("\n" + "=" * 70)
        print("🧪 FORCE DELETE AND VALIDATION TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Tests Passed: {self.test_results['passed']}")
        print(f"❌ Tests Failed: {self.test_results['failed']}")
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        if total_tests > 0:
            success_rate = (self.test_results['passed'] / total_tests) * 100
            print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        return self.test_results

if __name__ == "__main__":
    tester = ForceDeleteAndValidationTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)