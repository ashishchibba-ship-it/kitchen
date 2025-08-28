#!/usr/bin/env python3
"""
Backend API Testing for Production Kitchen Management System
Focus: Debugging specific user issues with delete and add functionality
Key Issues to Debug:
1. Delete Issues: User can't delete items they don't want anymore - getting error "cannot be deleted"
2. Adding Items Issues: User says they tried adding more items but "it just won't work"
"""

import requests
import json
from datetime import datetime, date, timedelta
import time
import sys

# Backend URL from frontend/.env
BASE_URL = "https://kitchen-manager-2.preview.emergentagent.com/api"

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

    def run_debug_tests(self):
        """Run all debug tests for the specific user issues"""
        print("🔍 STARTING DEBUG TESTS FOR USER ISSUES")
        print("=" * 60)
        
        # Debug the specific issues mentioned in the review request
        self.debug_delete_issues()
        self.debug_adding_items_issues()
        self.test_complete_crud_workflow()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🔍 DEBUG TEST SUMMARY")
        print("=" * 60)
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
    results = tester.run_debug_tests()
    
    # Exit with appropriate code
    if isinstance(results, dict) and results.get("failed", 0) == 0:
        print("\n🎉 All debug tests passed!")
        sys.exit(0)
    else:
        failed_count = results.get("failed", 1) if isinstance(results, dict) else 1
        print(f"\n💥 {failed_count} tests failed. Check the output above for details.")
        sys.exit(1)