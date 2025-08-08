#!/usr/bin/env python3
"""
Debug Test for Venue Users Not Seeing Items Issue
Focus: Diagnosing why venue users cannot see items in orderable-items endpoints

Test Plan:
1. Check current production items in the database - what statuses do they have?
2. Check which items have available_for_order > 0
3. Test the GET /api/orderable-items endpoint to see what items are returned
4. Test the GET /api/orderable-items/by-category endpoint 
5. Create a test production item, mark it as completed, set availability > 0, and verify it shows up in orderable items
"""

import requests
import json
from datetime import datetime, date
import sys

# Backend URL from frontend/.env
BASE_URL = "https://523e0c6c-09ea-4970-8dcd-e42fec7deab4.preview.emergentagent.com/api"

class VenueItemsDebugTester:
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
    
    def log_info(self, message):
        print(f"ℹ️  {message}")
    
    def check_current_production_items_status(self):
        """Check current production items in the database - what statuses do they have?"""
        print("\n=== Step 1: Checking Current Production Items Status ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                items = response.json()
                self.log_result("Fetch all production items", True, f"Found {len(items)} total items")
                
                if not items:
                    self.log_info("❗ NO PRODUCTION ITEMS FOUND IN DATABASE - This is likely the root cause!")
                    return []
                
                # Analyze status distribution
                status_counts = {}
                availability_counts = {"available_for_order_gt_0": 0, "available_for_order_eq_0": 0}
                
                self.log_info(f"\n📊 PRODUCTION ITEMS ANALYSIS ({len(items)} total items):")
                self.log_info("=" * 60)
                
                for i, item in enumerate(items, 1):
                    status = item.get("status", "unknown")
                    available_qty = item.get("available_for_order", 0)
                    
                    # Count statuses
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    # Count availability
                    if available_qty > 0:
                        availability_counts["available_for_order_gt_0"] += 1
                    else:
                        availability_counts["available_for_order_eq_0"] += 1
                    
                    # Log each item details
                    self.log_info(f"{i:2d}. {item.get('name', 'Unknown')} | Status: {status} | Available: {available_qty} | Category: {item.get('category', 'N/A')}")
                
                self.log_info("\n📈 STATUS SUMMARY:")
                for status, count in status_counts.items():
                    self.log_info(f"   • {status}: {count} items")
                
                self.log_info("\n📦 AVAILABILITY SUMMARY:")
                self.log_info(f"   • Items with available_for_order > 0: {availability_counts['available_for_order_gt_0']}")
                self.log_info(f"   • Items with available_for_order = 0: {availability_counts['available_for_order_eq_0']}")
                
                # Check for items that should be orderable (completed + available > 0)
                orderable_candidates = [
                    item for item in items 
                    if item.get("status") == "completed" and item.get("available_for_order", 0) > 0
                ]
                
                self.log_info(f"\n🎯 ITEMS THAT SHOULD BE ORDERABLE: {len(orderable_candidates)}")
                if orderable_candidates:
                    for item in orderable_candidates:
                        self.log_info(f"   • {item.get('name')} (Available: {item.get('available_for_order')})")
                else:
                    self.log_info("   ❗ NO ITEMS ARE BOTH COMPLETED AND HAVE AVAILABILITY > 0")
                    self.log_info("   This explains why venue users cannot see any items!")
                
                return items
                
            else:
                self.log_result("Fetch all production items", False, f"Status: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_result("Check Current Production Items Status", False, f"Exception: {str(e)}")
            return []
    
    def check_items_with_availability(self, items):
        """Check which items have available_for_order > 0"""
        print("\n=== Step 2: Checking Items with Availability > 0 ===")
        
        try:
            available_items = [item for item in items if item.get("available_for_order", 0) > 0]
            
            self.log_result("Filter items with availability > 0", True, f"Found {len(available_items)} items")
            
            if available_items:
                self.log_info("\n📋 ITEMS WITH AVAILABILITY > 0:")
                for item in available_items:
                    status = item.get("status", "unknown")
                    available_qty = item.get("available_for_order", 0)
                    self.log_info(f"   • {item.get('name')} | Status: {status} | Available: {available_qty}")
                    
                    if status != "completed":
                        self.log_info(f"     ⚠️  This item won't appear in orderable-items because status is '{status}', not 'completed'")
            else:
                self.log_info("❗ NO ITEMS HAVE available_for_order > 0")
                self.log_info("This is a major issue - managers need to set item availability!")
            
            return available_items
            
        except Exception as e:
            self.log_result("Check Items with Availability", False, f"Exception: {str(e)}")
            return []
    
    def test_orderable_items_endpoint(self):
        """Test the GET /api/orderable-items endpoint to see what items are returned"""
        print("\n=== Step 3: Testing GET /api/orderable-items Endpoint ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/orderable-items")
            if response.status_code == 200:
                orderable_items = response.json()
                self.log_result("GET /api/orderable-items", True, f"Returned {len(orderable_items)} items")
                
                if orderable_items:
                    self.log_info("\n🛒 ORDERABLE ITEMS RETURNED:")
                    for item in orderable_items:
                        self.log_info(f"   • {item.get('name')} | Category: {item.get('category')} | Available: {item.get('available_quantity')} | Price: ${item.get('unit_price')}")
                else:
                    self.log_info("❗ NO ORDERABLE ITEMS RETURNED")
                    self.log_info("This confirms the issue - venue users see no items because:")
                    self.log_info("   1. No items have status='completed' AND available_for_order > 0")
                    self.log_info("   2. The orderable-items endpoint filters for both conditions")
                
                return orderable_items
            else:
                self.log_result("GET /api/orderable-items", False, f"Status: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_result("Test Orderable Items Endpoint", False, f"Exception: {str(e)}")
            return []
    
    def test_orderable_items_by_category_endpoint(self):
        """Test the GET /api/orderable-items/by-category endpoint"""
        print("\n=== Step 4: Testing GET /api/orderable-items/by-category Endpoint ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
            if response.status_code == 200:
                items_by_category = response.json()
                self.log_result("GET /api/orderable-items/by-category", True, f"Returned {len(items_by_category)} categories")
                
                if items_by_category:
                    total_items = sum(len(items) for items in items_by_category.values())
                    self.log_info(f"\n📂 ITEMS BY CATEGORY ({total_items} total items):")
                    for category, items in items_by_category.items():
                        self.log_info(f"   • {category}: {len(items)} items")
                        for item in items:
                            self.log_info(f"     - {item.get('name')} (Available: {item.get('available_quantity')})")
                else:
                    self.log_info("❗ NO CATEGORIES WITH ORDERABLE ITEMS")
                    self.log_info("This confirms the same issue as the regular orderable-items endpoint")
                
                return items_by_category
            else:
                self.log_result("GET /api/orderable-items/by-category", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_result("Test Orderable Items by Category Endpoint", False, f"Exception: {str(e)}")
            return {}
    
    def create_test_production_item_and_verify(self):
        """Create a test production item, mark it as completed, set availability > 0, and verify it shows up in orderable items"""
        print("\n=== Step 5: Creating Test Item and Verifying Full Workflow ===")
        
        try:
            # Step 5a: Create a test production item
            test_item_data = {
                "name": "Debug Test Burger",
                "category": "Main Course",
                "quantity": 20,
                "unit_of_measure": "burgers",
                "assigned_staff": "chef_alice",
                "base_cost": 12.0
            }
            
            response = self.session.post(
                f"{BASE_URL}/production-items?created_by=manager",
                json=test_item_data
            )
            
            if response.status_code == 200:
                created_item = response.json()
                item_id = created_item["id"]
                self.log_result("Create test production item", True, f"Created '{test_item_data['name']}' with ID: {item_id}")
                
                # Verify initial status is 'pending' and available_for_order is 0
                initial_status = created_item.get("status")
                initial_availability = created_item.get("available_for_order", 0)
                self.log_info(f"   Initial status: {initial_status}, Initial availability: {initial_availability}")
                
                # Step 5b: Set availability > 0 (manager action)
                availability_data = {
                    "available_for_order": 15,
                    "unit_price": 18.50,
                    "availability_status": "available"
                }
                
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item_id}/availability",
                    json=availability_data
                )
                
                if response.status_code == 200:
                    self.log_result("Set item availability", True, f"Set available_for_order=15, unit_price=$18.50")
                    
                    # Step 5c: Mark item as completed (kitchen staff action)
                    response = self.session.put(
                        f"{BASE_URL}/production-items/{item_id}/status?status=completed"
                    )
                    
                    if response.status_code == 200:
                        self.log_result("Mark item as completed", True, "Status updated to 'completed'")
                        
                        # Step 5d: Verify item now appears in orderable-items
                        response = self.session.get(f"{BASE_URL}/orderable-items")
                        if response.status_code == 200:
                            orderable_items = response.json()
                            test_item_found = any(item["id"] == item_id for item in orderable_items)
                            
                            if test_item_found:
                                self.log_result("Verify item in orderable-items", True, "Test item now appears in orderable items!")
                                
                                # Find and display the item details
                                found_item = next(item for item in orderable_items if item["id"] == item_id)
                                self.log_info(f"   Found item details:")
                                self.log_info(f"   • Name: {found_item.get('name')}")
                                self.log_info(f"   • Category: {found_item.get('category')}")
                                self.log_info(f"   • Available Quantity: {found_item.get('available_quantity')}")
                                self.log_info(f"   • Unit Price: ${found_item.get('unit_price')}")
                                self.log_info(f"   • Availability Status: {found_item.get('availability_status')}")
                                
                                # Step 5e: Verify item appears in by-category endpoint
                                response = self.session.get(f"{BASE_URL}/orderable-items/by-category")
                                if response.status_code == 200:
                                    items_by_category = response.json()
                                    category = test_item_data["category"]
                                    
                                    if category in items_by_category:
                                        category_items = items_by_category[category]
                                        test_item_in_category = any(item["id"] == item_id for item in category_items)
                                        
                                        if test_item_in_category:
                                            self.log_result("Verify item in by-category endpoint", True, f"Test item appears in '{category}' category")
                                        else:
                                            self.log_result("Verify item in by-category endpoint", False, f"Test item not found in '{category}' category")
                                    else:
                                        self.log_result("Verify item in by-category endpoint", False, f"Category '{category}' not found in response")
                                else:
                                    self.log_result("Verify item in by-category endpoint", False, f"Status: {response.status_code}")
                                
                                # Success! The workflow works
                                self.log_info("\n🎉 SUCCESS! The orderable items workflow is working correctly!")
                                self.log_info("The issue is that existing items in the database are either:")
                                self.log_info("   1. Not marked as 'completed' status, OR")
                                self.log_info("   2. Don't have available_for_order > 0 set by manager")
                                
                                return True
                                
                            else:
                                self.log_result("Verify item in orderable-items", False, "Test item not found in orderable items")
                                self.log_info("❗ This indicates a bug in the orderable-items endpoint logic")
                                return False
                        else:
                            self.log_result("Verify item in orderable-items", False, f"Status: {response.status_code}")
                            return False
                    else:
                        self.log_result("Mark item as completed", False, f"Status: {response.status_code}")
                        return False
                else:
                    self.log_result("Set item availability", False, f"Status: {response.status_code}")
                    return False
            else:
                self.log_result("Create test production item", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Create Test Item and Verify Workflow", False, f"Exception: {str(e)}")
            return False
    
    def provide_diagnosis_and_solution(self):
        """Provide diagnosis and solution based on test results"""
        print("\n" + "=" * 80)
        print("🔍 DIAGNOSIS AND SOLUTION")
        print("=" * 80)
        
        self.log_info("Based on the test results, here's what's happening:")
        self.log_info("")
        self.log_info("🔍 ROOT CAUSE ANALYSIS:")
        self.log_info("The orderable-items endpoints filter items with TWO conditions:")
        self.log_info("   1. status = 'completed'")
        self.log_info("   2. available_for_order > 0")
        self.log_info("")
        self.log_info("If venue users cannot see items, it means:")
        self.log_info("   • Items exist but are not marked as 'completed' by kitchen staff, OR")
        self.log_info("   • Items are completed but managers haven't set available_for_order > 0, OR")
        self.log_info("   • No production items exist in the database at all")
        self.log_info("")
        self.log_info("💡 SOLUTION:")
        self.log_info("1. Kitchen staff must mark items as 'completed' after production")
        self.log_info("2. Managers must set available_for_order > 0 for items they want to sell")
        self.log_info("3. Both conditions must be met for items to appear in venue ordering interface")
        self.log_info("")
        self.log_info("🛠️  IMMEDIATE ACTIONS NEEDED:")
        self.log_info("1. Check existing production items and mark appropriate ones as 'completed'")
        self.log_info("2. Have managers set availability quantities for completed items")
        self.log_info("3. Verify the workflow: Create → Complete → Set Availability → Appears in Orderable Items")
    
    def run_debug_tests(self):
        """Run comprehensive debug tests for venue items visibility issue"""
        print("🔍 Starting Venue Items Debug Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Focus: Diagnosing why venue users cannot see items")
        print("=" * 80)
        
        # Step 1: Check current production items status
        items = self.check_current_production_items_status()
        
        # Step 2: Check items with availability > 0
        available_items = self.check_items_with_availability(items)
        
        # Step 3: Test orderable-items endpoint
        orderable_items = self.test_orderable_items_endpoint()
        
        # Step 4: Test orderable-items/by-category endpoint
        items_by_category = self.test_orderable_items_by_category_endpoint()
        
        # Step 5: Create test item and verify full workflow
        workflow_success = self.create_test_production_item_and_verify()
        
        # Provide diagnosis and solution
        self.provide_diagnosis_and_solution()
        
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
        
        return workflow_success

if __name__ == "__main__":
    tester = VenueItemsDebugTester()
    success = tester.run_debug_tests()
    sys.exit(0 if success else 1)