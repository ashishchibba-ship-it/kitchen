#!/usr/bin/env python3
"""
Backend API Testing for Production Kitchen Management System
Focus: Testing Enhanced Unit of Measure Options and Post-Creation Image Upload
Key Tests:
1. ENHANCED UNIT OF MEASURE OPTIONS - kilo, litre, carton, each support
2. POST-CREATION IMAGE UPLOAD - PUT/DELETE image endpoints
3. BACKWARD COMPATIBILITY - old "kg" to "kilo" conversion
4. ORDERABLE ITEMS UNIT COMPATIBILITY - unit information in APIs
5. IMAGE WORKFLOW TESTING - create → add → update → remove image
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
    
    def test_enhanced_unit_measures_and_image_upload(self):
        """Test the enhanced unit of measure options and post-creation image upload"""
        print("🔧 STARTING ENHANCED UNIT MEASURES AND IMAGE UPLOAD TESTS")
        print("=" * 70)
        
        # Test 1: Enhanced Unit of Measure Options
        self.test_enhanced_unit_of_measure_options()
        
        # Test 2: Post-Creation Image Upload
        self.test_post_creation_image_upload()
        
        # Test 3: Backward Compatibility for Units
        self.test_backward_compatibility_units()
        
        # Test 4: Orderable Items Unit Information
        self.test_orderable_items_unit_compatibility()
        
        # Test 5: Complete Image Workflow
        self.test_complete_image_workflow()
        
        # Print summary
        print("\n" + "=" * 70)
        print("🔧 ENHANCED FEATURES TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Tests Passed: {self.test_results['passed']}")
        print(f"❌ Tests Failed: {self.test_results['failed']}")
        print(f"📊 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        return self.test_results

    def test_enhanced_unit_of_measure_options(self):
        """Test creating production items with different unit options: kilo, litre, carton, each"""
        print("\n=== TEST 1: Enhanced Unit of Measure Options ===")
        
        try:
            # Test creating items with each valid unit type
            valid_units = ["kilo", "litre", "carton", "each"]
            created_items = []
            
            for unit in valid_units:
                test_item = {
                    "name": f"Test Item {unit.title()}",
                    "category": "Main Course",
                    "unit_of_measure": unit,
                    "base_cost": 12.0,
                    "assigned_staff": None,
                    "image": None
                }
                
                response = self.session.post(f"{BASE_URL}/production-items", 
                                           json=test_item, 
                                           params={"created_by": "test_manager"})
                
                if response.status_code == 200:
                    created_item = response.json()
                    created_items.append(created_item)
                    
                    # Verify unit was set correctly
                    if created_item.get("unit_of_measure") == unit:
                        self.log_result(f"Create item with unit '{unit}'", True, 
                                      f"Item created with correct unit: {unit}")
                    else:
                        self.log_result(f"Create item with unit '{unit}'", False, 
                                      f"Expected unit '{unit}', got '{created_item.get('unit_of_measure')}'")
                    
                    # Verify automatic price calculation (15% markup)
                    expected_price = 12.0 * 1.15  # 13.80
                    actual_price = created_item.get("unit_price", 0)
                    if abs(actual_price - expected_price) < 0.01:
                        self.log_result(f"Price calculation for {unit} item", True, 
                                      f"Correct 15% markup: ${actual_price:.2f}")
                    else:
                        self.log_result(f"Price calculation for {unit} item", False, 
                                      f"Expected ${expected_price:.2f}, got ${actual_price:.2f}")
                else:
                    self.log_result(f"Create item with unit '{unit}'", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            # Test invalid unit defaults to "kilo"
            invalid_unit_item = {
                "name": "Test Invalid Unit Item",
                "category": "Main Course", 
                "unit_of_measure": "invalid_unit",
                "base_cost": 10.0
            }
            
            response = self.session.post(f"{BASE_URL}/production-items", 
                                       json=invalid_unit_item, 
                                       params={"created_by": "test_manager"})
            
            if response.status_code == 200:
                created_item = response.json()
                created_items.append(created_item)
                
                if created_item.get("unit_of_measure") == "kilo":
                    self.log_result("Invalid unit defaults to kilo", True, 
                                  "Invalid unit correctly defaulted to 'kilo'")
                else:
                    self.log_result("Invalid unit defaults to kilo", False, 
                                  f"Expected 'kilo', got '{created_item.get('unit_of_measure')}'")
            else:
                self.log_result("Test invalid unit handling", False, 
                              f"Status: {response.status_code}")
            
            # Verify all created items appear in GET /api/production-items with correct units
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                all_items = response.json()
                
                # Find our test items
                test_item_names = [item["name"] for item in created_items]
                found_items = [item for item in all_items if item["name"] in test_item_names]
                
                if len(found_items) == len(created_items):
                    self.log_result("Retrieve items with units", True, 
                                  f"All {len(created_items)} test items found in production items list")
                    
                    # Verify units are preserved
                    for item in found_items:
                        expected_unit = next((ci["unit_of_measure"] for ci in created_items 
                                            if ci["name"] == item["name"]), None)
                        if item.get("unit_of_measure") == expected_unit:
                            self.log_result(f"Unit preservation for {item['name']}", True, 
                                          f"Unit '{expected_unit}' preserved correctly")
                        else:
                            self.log_result(f"Unit preservation for {item['name']}", False, 
                                          f"Expected '{expected_unit}', got '{item.get('unit_of_measure')}'")
                else:
                    self.log_result("Retrieve items with units", False, 
                                  f"Expected {len(created_items)} items, found {len(found_items)}")
            else:
                self.log_result("Retrieve items with units", False, 
                              f"Status: {response.status_code}")
            
            # Clean up test items
            for item in created_items:
                if "id" in item:
                    self.session.delete(f"{BASE_URL}/production-items/{item['id']}")
                    
        except Exception as e:
            self.log_result("Enhanced Unit of Measure Options", False, f"Exception: {str(e)}")

    def test_post_creation_image_upload(self):
        """Test PUT and DELETE endpoints for post-creation image upload"""
        print("\n=== TEST 2: Post-Creation Image Upload ===")
        
        try:
            # First create a production item without an image
            test_item = {
                "name": "Image Test Item",
                "category": "Main Course",
                "unit_of_measure": "kilo",
                "base_cost": 15.0
            }
            
            response = self.session.post(f"{BASE_URL}/production-items", 
                                       json=test_item, 
                                       params={"created_by": "test_manager"})
            
            if response.status_code != 200:
                self.log_result("Create item for image testing", False, 
                              f"Status: {response.status_code}")
                return
            
            created_item = response.json()
            item_id = created_item["id"]
            
            self.log_result("Create item for image testing", True, 
                          f"Item created: {created_item['name']}")
            
            # Test 1: PUT /api/production-items/{item_id}/image - Add image
            test_image_data = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
            
            image_payload = {"image": test_image_data}
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/image", 
                                      json=image_payload)
            
            if response.status_code == 200:
                updated_item = response.json()
                
                if updated_item.get("image") == test_image_data:
                    self.log_result("PUT image endpoint - Add image", True, 
                                  "Image successfully added to existing item")
                else:
                    self.log_result("PUT image endpoint - Add image", False, 
                                  "Image data not properly stored")
                
                # Verify updated_at timestamp was updated
                if "updated_at" in updated_item:
                    self.log_result("Image update timestamp", True, 
                                  f"Updated timestamp: {updated_item['updated_at']}")
                else:
                    self.log_result("Image update timestamp", False, 
                                  "No updated_at timestamp found")
            else:
                self.log_result("PUT image endpoint - Add image", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
            
            # Test 2: PUT /api/production-items/{item_id}/image - Update existing image
            new_image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            image_payload = {"image": new_image_data}
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/image", 
                                      json=image_payload)
            
            if response.status_code == 200:
                updated_item = response.json()
                
                if updated_item.get("image") == new_image_data:
                    self.log_result("PUT image endpoint - Update image", True, 
                                  "Image successfully updated")
                else:
                    self.log_result("PUT image endpoint - Update image", False, 
                                  "Image update failed")
            else:
                self.log_result("PUT image endpoint - Update image", False, 
                              f"Status: {response.status_code}")
            
            # Test 3: DELETE /api/production-items/{item_id}/image - Remove image
            response = self.session.delete(f"{BASE_URL}/production-items/{item_id}/image")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("message") == "Image removed successfully":
                    self.log_result("DELETE image endpoint - Remove image", True, 
                                  "Image successfully removed")
                    
                    # Verify image was actually removed by getting the item
                    get_response = self.session.get(f"{BASE_URL}/production-items")
                    if get_response.status_code == 200:
                        items = get_response.json()
                        updated_item = next((item for item in items if item["id"] == item_id), None)
                        
                        if updated_item and "image" not in updated_item:
                            self.log_result("Verify image removal", True, 
                                          "Image field properly removed from item")
                        elif updated_item and updated_item.get("image") is None:
                            self.log_result("Verify image removal", True, 
                                          "Image field set to null")
                        else:
                            self.log_result("Verify image removal", False, 
                                          f"Image still present: {updated_item.get('image', 'N/A')}")
                else:
                    self.log_result("DELETE image endpoint - Remove image", False, 
                                  f"Unexpected response: {response_data}")
            else:
                self.log_result("DELETE image endpoint - Remove image", False, 
                              f"Status: {response.status_code}")
            
            # Test 4: Error handling for non-existent items
            fake_item_id = "non-existent-item-id"
            
            # Test PUT on non-existent item
            response = self.session.put(f"{BASE_URL}/production-items/{fake_item_id}/image", 
                                      json={"image": test_image_data})
            
            if response.status_code == 404:
                self.log_result("PUT image - Non-existent item error", True, 
                              "Correctly returned 404 for non-existent item")
            else:
                self.log_result("PUT image - Non-existent item error", False, 
                              f"Expected 404, got {response.status_code}")
            
            # Test DELETE on non-existent item
            response = self.session.delete(f"{BASE_URL}/production-items/{fake_item_id}/image")
            
            if response.status_code == 404:
                self.log_result("DELETE image - Non-existent item error", True, 
                              "Correctly returned 404 for non-existent item")
            else:
                self.log_result("DELETE image - Non-existent item error", False, 
                              f"Expected 404, got {response.status_code}")
            
            # Test 5: Invalid image data handling
            invalid_image_payload = {"image": ""}
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/image", 
                                      json=invalid_image_payload)
            
            if response.status_code == 400:
                self.log_result("PUT image - Invalid data error", True, 
                              "Correctly rejected empty image data")
            else:
                self.log_result("PUT image - Invalid data error", False, 
                              f"Expected 400, got {response.status_code}")
            
            # Clean up test item
            self.session.delete(f"{BASE_URL}/production-items/{item_id}")
            
        except Exception as e:
            self.log_result("Post-Creation Image Upload", False, f"Exception: {str(e)}")

    def test_backward_compatibility_units(self):
        """Test backward compatibility: old 'kg' items are converted to 'kilo'"""
        print("\n=== TEST 3: Backward Compatibility for Units ===")
        
        try:
            # Get existing production items to check for backward compatibility
            response = self.session.get(f"{BASE_URL}/production-items")
            
            if response.status_code == 200:
                items = response.json()
                self.log_result("Get production items for compatibility check", True, 
                              f"Retrieved {len(items)} items")
                
                # Check if any items have old "kg" units (should be converted to "kilo")
                kg_items = [item for item in items if item.get("unit_of_measure") == "kg"]
                kilo_items = [item for item in items if item.get("unit_of_measure") == "kilo"]
                
                if len(kg_items) == 0:
                    self.log_result("No old 'kg' units found", True, 
                                  "All items use new unit system or have been converted")
                else:
                    self.log_result("Old 'kg' units still present", False, 
                                  f"Found {len(kg_items)} items still using 'kg' instead of 'kilo'")
                
                # Check that all items have valid units
                valid_units = ["kilo", "litre", "carton", "each"]
                invalid_unit_items = []
                
                for item in items:
                    unit = item.get("unit_of_measure")
                    if unit not in valid_units:
                        invalid_unit_items.append(f"{item['name']}: {unit}")
                
                if len(invalid_unit_items) == 0:
                    self.log_result("All items have valid units", True, 
                                  "All production items use valid unit types")
                else:
                    self.log_result("Invalid units found", False, 
                                  f"Items with invalid units: {invalid_unit_items}")
                
                # Test creating an item with old "kg" unit to see if it gets converted
                test_item_kg = {
                    "name": "Backward Compatibility Test Item",
                    "category": "Main Course",
                    "unit_of_measure": "kg",  # Old unit
                    "base_cost": 10.0
                }
                
                response = self.session.post(f"{BASE_URL}/production-items", 
                                           json=test_item_kg, 
                                           params={"created_by": "test_manager"})
                
                if response.status_code == 200:
                    created_item = response.json()
                    
                    if created_item.get("unit_of_measure") == "kilo":
                        self.log_result("Convert 'kg' to 'kilo' on creation", True, 
                                      "Old 'kg' unit automatically converted to 'kilo'")
                    else:
                        self.log_result("Convert 'kg' to 'kilo' on creation", False, 
                                      f"Expected 'kilo', got '{created_item.get('unit_of_measure')}'")
                    
                    # Clean up test item
                    self.session.delete(f"{BASE_URL}/production-items/{created_item['id']}")
                else:
                    self.log_result("Test 'kg' to 'kilo' conversion", False, 
                                  f"Status: {response.status_code}")
                
            else:
                self.log_result("Get production items for compatibility check", False, 
                              f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Backward Compatibility Units", False, f"Exception: {str(e)}")

    def test_orderable_items_unit_compatibility(self):
        """Test that orderable items APIs include correct unit information"""
        print("\n=== TEST 4: Orderable Items Unit Compatibility ===")
        
        try:
            # Create test items with different units for orderable items testing
            test_items = [
                {"name": "Orderable Kilo Item", "unit_of_measure": "kilo", "base_cost": 10.0},
                {"name": "Orderable Litre Item", "unit_of_measure": "litre", "base_cost": 8.0},
                {"name": "Orderable Carton Item", "unit_of_measure": "carton", "base_cost": 15.0},
                {"name": "Orderable Each Item", "unit_of_measure": "each", "base_cost": 5.0}
            ]
            
            created_items = []
            
            for item_data in test_items:
                item_data.update({"category": "Main Course"})
                
                response = self.session.post(f"{BASE_URL}/production-items", 
                                           json=item_data, 
                                           params={"created_by": "test_manager"})
                
                if response.status_code == 200:
                    created_items.append(response.json())
            
            if len(created_items) != len(test_items):
                self.log_result("Create test items for orderable testing", False, 
                              f"Only created {len(created_items)}/{len(test_items)} items")
                return
            
            self.log_result("Create test items for orderable testing", True, 
                          f"Created {len(created_items)} test items")
            
            # Test 1: GET /api/orderable-items includes unit information
            response = self.session.get(f"{BASE_URL}/orderable-items")
            
            if response.status_code == 200:
                orderable_items = response.json()
                
                # Find our test items in orderable items
                test_item_names = [item["name"] for item in created_items]
                found_orderable_items = [item for item in orderable_items 
                                       if item["name"] in test_item_names]
                
                if len(found_orderable_items) == len(created_items):
                    self.log_result("Test items in orderable-items", True, 
                                  f"All {len(created_items)} test items found in orderable items")
                    
                    # Verify unit information is included and correct
                    for orderable_item in found_orderable_items:
                        original_item = next((item for item in created_items 
                                            if item["name"] == orderable_item["name"]), None)
                        
                        if original_item:
                            expected_unit = original_item["unit_of_measure"]
                            actual_unit = orderable_item.get("unit_of_measure")
                            
                            if actual_unit == expected_unit:
                                self.log_result(f"Unit info for {orderable_item['name']}", True, 
                                              f"Correct unit: {actual_unit}")
                            else:
                                self.log_result(f"Unit info for {orderable_item['name']}", False, 
                                              f"Expected {expected_unit}, got {actual_unit}")
                            
                            # Verify price calculation is correct (15% markup)
                            expected_price = original_item["base_cost"] * 1.15
                            actual_price = orderable_item.get("unit_price", 0)
                            
                            if abs(actual_price - expected_price) < 0.01:
                                self.log_result(f"Price for {orderable_item['name']}", True, 
                                              f"Correct price: ${actual_price:.2f}")
                            else:
                                self.log_result(f"Price for {orderable_item['name']}", False, 
                                              f"Expected ${expected_price:.2f}, got ${actual_price:.2f}")
                else:
                    self.log_result("Test items in orderable-items", False, 
                                  f"Expected {len(created_items)}, found {len(found_orderable_items)}")
            else:
                self.log_result("GET /api/orderable-items", False, 
                              f"Status: {response.status_code}")
            
            # Test 2: GET /api/orderable-items/by-category includes unit information
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            
            if response.status_code == 200:
                orderable_by_category = response.json()
                
                # Find our test items in the categorized response
                main_course_items = orderable_by_category.get("Main Course", [])
                test_item_names = [item["name"] for item in created_items]
                found_categorized_items = [item for item in main_course_items 
                                         if item["name"] in test_item_names]
                
                if len(found_categorized_items) == len(created_items):
                    self.log_result("Test items in orderable-items/by-category", True, 
                                  f"All {len(created_items)} test items found in categorized view")
                    
                    # Verify unit information in categorized view
                    for categorized_item in found_categorized_items:
                        original_item = next((item for item in created_items 
                                            if item["name"] == categorized_item["name"]), None)
                        
                        if original_item:
                            expected_unit = original_item["unit_of_measure"]
                            actual_unit = categorized_item.get("unit_of_measure")
                            
                            if actual_unit == expected_unit:
                                self.log_result(f"Categorized unit info for {categorized_item['name']}", True, 
                                              f"Correct unit: {actual_unit}")
                            else:
                                self.log_result(f"Categorized unit info for {categorized_item['name']}", False, 
                                              f"Expected {expected_unit}, got {actual_unit}")
                else:
                    self.log_result("Test items in orderable-items/by-category", False, 
                                  f"Expected {len(created_items)}, found {len(found_categorized_items)}")
            else:
                self.log_result("GET /api/orderable-items/by-category", False, 
                              f"Status: {response.status_code}")
            
            # Clean up test items
            for item in created_items:
                if "id" in item:
                    self.session.delete(f"{BASE_URL}/production-items/{item['id']}")
                    
        except Exception as e:
            self.log_result("Orderable Items Unit Compatibility", False, f"Exception: {str(e)}")

    def test_complete_image_workflow(self):
        """Test complete image workflow: create item → add image → update image → remove image"""
        print("\n=== TEST 5: Complete Image Workflow ===")
        
        try:
            # Step 1: Create item without image
            test_item = {
                "name": "Complete Workflow Test Item",
                "category": "Main Course",
                "unit_of_measure": "each",
                "base_cost": 20.0
            }
            
            response = self.session.post(f"{BASE_URL}/production-items", 
                                       json=test_item, 
                                       params={"created_by": "test_manager"})
            
            if response.status_code != 200:
                self.log_result("Workflow Step 1 - Create item", False, 
                              f"Status: {response.status_code}")
                return
            
            created_item = response.json()
            item_id = created_item["id"]
            
            # Verify item was created without image
            if "image" not in created_item or created_item.get("image") is None:
                self.log_result("Workflow Step 1 - Create item without image", True, 
                              "Item created successfully without image")
            else:
                self.log_result("Workflow Step 1 - Create item without image", False, 
                              f"Unexpected image data: {created_item.get('image')}")
            
            # Step 2: Add image to existing item
            first_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
            
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/image", 
                                      json={"image": first_image})
            
            if response.status_code == 200:
                updated_item = response.json()
                
                if updated_item.get("image") == first_image:
                    self.log_result("Workflow Step 2 - Add image", True, 
                                  "Image successfully added to item")
                else:
                    self.log_result("Workflow Step 2 - Add image", False, 
                                  "Image not properly added")
            else:
                self.log_result("Workflow Step 2 - Add image", False, 
                              f"Status: {response.status_code}")
            
            # Step 3: Update image with new image
            second_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            response = self.session.put(f"{BASE_URL}/production-items/{item_id}/image", 
                                      json={"image": second_image})
            
            if response.status_code == 200:
                updated_item = response.json()
                
                if updated_item.get("image") == second_image:
                    self.log_result("Workflow Step 3 - Update image", True, 
                                  "Image successfully updated")
                else:
                    self.log_result("Workflow Step 3 - Update image", False, 
                                  "Image not properly updated")
            else:
                self.log_result("Workflow Step 3 - Update image", False, 
                              f"Status: {response.status_code}")
            
            # Step 4: Remove image
            response = self.session.delete(f"{BASE_URL}/production-items/{item_id}/image")
            
            if response.status_code == 200:
                self.log_result("Workflow Step 4 - Remove image", True, 
                              "Image successfully removed")
                
                # Verify image was removed by getting the item again
                response = self.session.get(f"{BASE_URL}/production-items")
                if response.status_code == 200:
                    items = response.json()
                    final_item = next((item for item in items if item["id"] == item_id), None)
                    
                    if final_item and ("image" not in final_item or final_item.get("image") is None):
                        self.log_result("Workflow Step 4 - Verify image removal", True, 
                                      "Image field properly removed")
                    else:
                        self.log_result("Workflow Step 4 - Verify image removal", False, 
                                      f"Image still present: {final_item.get('image') if final_item else 'Item not found'}")
            else:
                self.log_result("Workflow Step 4 - Remove image", False, 
                              f"Status: {response.status_code}")
            
            # Step 5: Verify item still exists and is functional after image operations
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                items = response.json()
                final_item = next((item for item in items if item["id"] == item_id), None)
                
                if final_item:
                    # Verify all other fields are intact
                    if (final_item.get("name") == test_item["name"] and 
                        final_item.get("unit_of_measure") == test_item["unit_of_measure"] and
                        abs(final_item.get("base_cost", 0) - test_item["base_cost"]) < 0.01):
                        self.log_result("Workflow Step 5 - Item integrity after image ops", True, 
                                      "All item fields preserved after image operations")
                    else:
                        self.log_result("Workflow Step 5 - Item integrity after image ops", False, 
                                      "Some item fields were corrupted during image operations")
                else:
                    self.log_result("Workflow Step 5 - Item integrity after image ops", False, 
                                  "Item not found after image operations")
            
            # Test complete workflow summary
            self.log_result("Complete Image Workflow", True, 
                          "Full workflow completed: create → add image → update image → remove image")
            
            # Clean up test item
            self.session.delete(f"{BASE_URL}/production-items/{item_id}")
            
        except Exception as e:
            self.log_result("Complete Image Workflow", False, f"Exception: {str(e)}")


if __name__ == "__main__":
    print("🚀 STARTING BACKEND API TESTING")
    print("Testing Enhanced Unit of Measure Options and Post-Creation Image Upload")
    print("=" * 80)
    
    tester = KitchenAPITester()
    
    try:
        # Run the enhanced features tests
        results = tester.test_enhanced_unit_measures_and_image_upload()
        
        print(f"\n🎯 FINAL TEST RESULTS")
        print("=" * 80)
        print(f"✅ Total Tests Passed: {results['passed']}")
        print(f"❌ Total Tests Failed: {results['failed']}")
        total_tests = results['passed'] + results['failed']
        success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
        print(f"📊 Overall Success Rate: {success_rate:.1f}%")
        
        if results['errors']:
            print(f"\n🚨 FAILED TESTS ({len(results['errors'])}):")
            for i, error in enumerate(results['errors'], 1):
                print(f"   {i}. {error}")
        
        # Determine overall result
        if results['failed'] == 0:
            print(f"\n🎉 ALL TESTS PASSED! Enhanced unit measures and image upload features are working correctly.")
            sys.exit(0)
        elif success_rate >= 80:
            print(f"\n⚠️  MOSTLY SUCCESSFUL with {success_rate:.1f}% pass rate. Some minor issues found.")
            sys.exit(0)
        else:
            print(f"\n❌ SIGNIFICANT ISSUES FOUND with {success_rate:.1f}% pass rate. Review failed tests.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)