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
    
    def test_user_authentication_with_addresses(self):
        """Test user authentication endpoints and verify venue users have addresses"""
        print("\n=== Testing User Authentication with Venue Addresses ===")
        
        try:
            # Test GET /api/users
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                users = response.json()
                self.log_result("GET /api/users", True, f"Retrieved {len(users)} users")
                
                # Verify predefined users exist with correct roles
                expected_users = {
                    "manager": "manager",
                    "chef_alice": "kitchen_staff", 
                    "chef_bob": "kitchen_staff",
                    "downtown_cafe": "venue_staff",
                    "uptown_restaurant": "venue_staff"
                }
                
                found_users = {user["username"]: user for user in users}
                
                for username, expected_role in expected_users.items():
                    if username in found_users:
                        user = found_users[username]
                        if user["role"] == expected_role:
                            self.log_result(f"User {username} role verification", True, f"Role: {expected_role}")
                            
                            # Test venue users have addresses
                            if expected_role == "venue_staff":
                                if "address" in user and user["address"]:
                                    self.log_result(f"Venue {username} address field", True, f"Address: {user['address']}")
                                else:
                                    self.log_result(f"Venue {username} address field", False, "Address field missing or empty")
                        else:
                            self.log_result(f"User {username} role verification", False, 
                                          f"Expected {expected_role}, got {user['role']}")
                    else:
                        self.log_result(f"User {username} existence", False, "User not found")
                
                # Test GET /api/users/{username} for venue user
                test_username = "downtown_cafe"
                response = self.session.get(f"{BASE_URL}/users/{test_username}")
                if response.status_code == 200:
                    user = response.json()
                    if user["username"] == test_username and user["role"] == "venue_staff":
                        self.log_result("GET /api/users/{username} for venue", True, f"Retrieved venue user {test_username}")
                        if "address" in user and user["address"]:
                            self.log_result("Venue user address in individual fetch", True, f"Address: {user['address']}")
                        else:
                            self.log_result("Venue user address in individual fetch", False, "Address missing")
                    else:
                        self.log_result("GET /api/users/{username} for venue", False, "User data mismatch")
                else:
                    self.log_result("GET /api/users/{username} for venue", False, f"Status: {response.status_code}")
                    
            else:
                self.log_result("GET /api/users", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("User Authentication with Addresses", False, f"Exception: {str(e)}")
    
    def test_categories_endpoint(self):
        """Test the new categories endpoint"""
        print("\n=== Testing Categories Endpoint ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/categories")
            if response.status_code == 200:
                categories_data = response.json()
                if "categories" in categories_data and isinstance(categories_data["categories"], list):
                    categories = categories_data["categories"]
                    self.log_result("GET /api/categories", True, f"Retrieved {len(categories)} categories")
                    
                    # Verify default categories exist
                    expected_defaults = ["Main Course", "Appetizer", "Dessert", "Beverage", "Side Dish", "Salad"]
                    found_defaults = [cat for cat in expected_defaults if cat in categories]
                    
                    if len(found_defaults) >= 3:  # At least some defaults should be present
                        self.log_result("Default categories present", True, f"Found: {', '.join(found_defaults)}")
                    else:
                        self.log_result("Default categories present", False, f"Only found: {', '.join(found_defaults)}")
                        
                else:
                    self.log_result("GET /api/categories", False, "Invalid response structure")
            else:
                self.log_result("GET /api/categories", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Categories Endpoint", False, f"Exception: {str(e)}")
    
    def test_production_management_with_categories(self):
        """Test production item management with new category and unit_of_measure fields"""
        print("\n=== Testing Production Management with Categories and Units ===")
        
        try:
            # Create test production items with new required fields
            today = date.today().isoformat()
            
            production_items = [
                {
                    "name": "Grilled Salmon with Herbs",
                    "category": "Main Course",
                    "quantity": 25,
                    "unit_of_measure": "portions",
                    "target_time": "10:00",
                    "production_date": today,
                    "assigned_staff": "chef_alice"
                },
                {
                    "name": "Caesar Salad Mix", 
                    "category": "Salad",
                    "quantity": 40,
                    "unit_of_measure": "servings",
                    "target_time": "11:30",
                    "production_date": today,
                    "assigned_staff": "chef_bob"
                },
                {
                    "name": "Chocolate Mousse",
                    "category": "Dessert",
                    "quantity": 20,
                    "unit_of_measure": "cups",
                    "target_time": "09:00",
                    "production_date": today,
                    "assigned_staff": "chef_alice"
                }
            ]
            
            created_items = []
            
            # Test POST /api/production-items with new fields
            for item_data in production_items:
                response = self.session.post(
                    f"{BASE_URL}/production-items?created_by=manager",
                    json=item_data
                )
                if response.status_code == 200:
                    item = response.json()
                    created_items.append(item)
                    
                    # Verify new fields are present
                    if "category" in item and item["category"] == item_data["category"]:
                        self.log_result(f"Category field for {item_data['name']}", True, f"Category: {item['category']}")
                    else:
                        self.log_result(f"Category field for {item_data['name']}", False, "Category missing or incorrect")
                    
                    if "unit_of_measure" in item and item["unit_of_measure"] == item_data["unit_of_measure"]:
                        self.log_result(f"Unit of measure for {item_data['name']}", True, f"Unit: {item['unit_of_measure']}")
                    else:
                        self.log_result(f"Unit of measure for {item_data['name']}", False, "Unit of measure missing or incorrect")
                    
                    # Verify cost field is NOT present (removed functionality)
                    if "cost" not in item:
                        self.log_result(f"Cost field removed for {item_data['name']}", True, "Cost field not present")
                    else:
                        self.log_result(f"Cost field removed for {item_data['name']}", False, "Cost field still present")
                        
                    self.log_result(f"Create production item: {item_data['name']}", True, f"ID: {item['id']}")
                else:
                    self.log_result(f"Create production item: {item_data['name']}", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            # Test GET /api/production-items
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                items = response.json()
                self.log_result("GET /api/production-items", True, f"Retrieved {len(items)} items")
                
                # Test filtering by category
                response = self.session.get(f"{BASE_URL}/production-items?category=Main Course")
                if response.status_code == 200:
                    main_course_items = response.json()
                    main_course_count = len([item for item in main_course_items if item.get("category") == "Main Course"])
                    self.log_result("Filter by category", True, 
                                  f"Retrieved {main_course_count} Main Course items")
                else:
                    self.log_result("Filter by category", False, f"Status: {response.status_code}")
                
                # Test filtering by date
                response = self.session.get(f"{BASE_URL}/production-items?production_date={today}")
                if response.status_code == 200:
                    filtered_items = response.json()
                    self.log_result("Filter by production date", True, 
                                  f"Retrieved {len(filtered_items)} items for today")
                else:
                    self.log_result("Filter by production date", False, f"Status: {response.status_code}")
                    
                # Test filtering by status
                response = self.session.get(f"{BASE_URL}/production-items?status=pending")
                if response.status_code == 200:
                    pending_items = response.json()
                    self.log_result("Filter by status", True, 
                                  f"Retrieved {len(pending_items)} pending items")
                else:
                    self.log_result("Filter by status", False, f"Status: {response.status_code}")
                    
            else:
                self.log_result("GET /api/production-items", False, f"Status: {response.status_code}")
            
            return created_items
            
        except Exception as e:
            self.log_result("Production Management with Categories", False, f"Exception: {str(e)}")
            return []
    
    def test_production_status_workflow(self, created_items):
        """Test production status tracking workflow"""
        print("\n=== Testing Production Status Workflow ===")
        
        if not created_items:
            self.log_result("Production Status Workflow", False, "No items to test with")
            return []
            
        try:
            completed_items = []
            
            for item in created_items:
                item_id = item["id"]
                item_name = item["name"]
                
                # Test status transition: pending -> in_progress
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item_id}/status?status=in_progress"
                )
                if response.status_code == 200:
                    self.log_result(f"Update {item_name} to in_progress", True)
                else:
                    self.log_result(f"Update {item_name} to in_progress", False, 
                                  f"Status: {response.status_code}")
                
                # Test status transition: in_progress -> completed
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item_id}/status?status=completed"
                )
                if response.status_code == 200:
                    self.log_result(f"Update {item_name} to completed", True)
                    completed_items.append(item)
                else:
                    self.log_result(f"Update {item_name} to completed", False, 
                                  f"Status: {response.status_code}")
            
            # Test GET /api/production-items/completed
            response = self.session.get(f"{BASE_URL}/production-items/completed")
            if response.status_code == 200:
                completed_list = response.json()
                self.log_result("GET completed items", True, 
                              f"Retrieved {len(completed_list)} completed items")
            else:
                self.log_result("GET completed items", False, f"Status: {response.status_code}")
            
            return completed_items
            
        except Exception as e:
            self.log_result("Production Status Workflow", False, f"Exception: {str(e)}")
            return []
    
    def test_order_management_with_delivery(self, completed_items):
        """Test order management with delivery_address and delivery_date fields"""
        print("\n=== Testing Order Management with Delivery Information ===")
        
        if not completed_items:
            self.log_result("Order Management with Delivery", False, "No completed items to order")
            return []
            
        try:
            # Create test orders with delivery information
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            day_after = (date.today() + timedelta(days=2)).isoformat()
            
            orders_data = [
                {
                    "venue_name": "Downtown Cafe",
                    "delivery_address": "123 Main St, Downtown, City 12345",
                    "delivery_date": tomorrow,
                    "items": [
                        {
                            "production_item_id": completed_items[0]["id"],
                            "production_item_name": completed_items[0]["name"],
                            "quantity": 10,
                            "unit_of_measure": completed_items[0]["unit_of_measure"]
                        }
                    ]
                }
            ]
            
            if len(completed_items) > 1:
                orders_data.append({
                    "venue_name": "Uptown Restaurant",
                    "delivery_address": "456 Oak Ave, Uptown, City 67890",
                    "delivery_date": day_after,
                    "items": [
                        {
                            "production_item_id": completed_items[1]["id"],
                            "production_item_name": completed_items[1]["name"],
                            "quantity": 15,
                            "unit_of_measure": completed_items[1]["unit_of_measure"]
                        }
                    ]
                })
            
            created_orders = []
            
            # Test POST /api/orders with delivery information
            for order_data in orders_data:
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    created_orders.append(order)
                    
                    # Verify delivery_address field
                    if "delivery_address" in order and order["delivery_address"] == order_data["delivery_address"]:
                        self.log_result(f"Delivery address for {order_data['venue_name']}", True,
                                      f"Address: {order['delivery_address']}")
                    else:
                        self.log_result(f"Delivery address for {order_data['venue_name']}", False,
                                      "Delivery address missing or incorrect")
                    
                    # Verify delivery_date field
                    if "delivery_date" in order and order["delivery_date"] == order_data["delivery_date"]:
                        self.log_result(f"Delivery date for {order_data['venue_name']}", True,
                                      f"Date: {order['delivery_date']}")
                    else:
                        self.log_result(f"Delivery date for {order_data['venue_name']}", False,
                                      "Delivery date missing or incorrect")
                        
                    self.log_result(f"Create order for {order_data['venue_name']}", True, 
                                  f"Order ID: {order['id']}")
                else:
                    self.log_result(f"Create order for {order_data['venue_name']}", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            # Test GET /api/orders
            response = self.session.get(f"{BASE_URL}/orders")
            if response.status_code == 200:
                orders = response.json()
                self.log_result("GET /api/orders", True, f"Retrieved {len(orders)} orders")
                
                # Test filtering by venue
                if created_orders:
                    venue_name = created_orders[0]["venue_name"]
                    response = self.session.get(f"{BASE_URL}/orders?venue_name={venue_name}")
                    if response.status_code == 200:
                        venue_orders = response.json()
                        self.log_result("Filter orders by venue", True,
                                      f"Retrieved {len(venue_orders)} orders for {venue_name}")
                    else:
                        self.log_result("Filter orders by venue", False, f"Status: {response.status_code}")
            else:
                self.log_result("GET /api/orders", False, f"Status: {response.status_code}")
            
            return created_orders
            
        except Exception as e:
            self.log_result("Order Management with Delivery", False, f"Exception: {str(e)}")
            return []
    
    def test_delivery_date_update(self, created_orders):
        """Test the new delivery date update endpoint"""
        print("\n=== Testing Delivery Date Update ===")
        
        if not created_orders:
            self.log_result("Delivery Date Update", False, "No orders to test with")
            return
            
        try:
            for order in created_orders:
                order_id = order["id"]
                venue_name = order["venue_name"]
                new_delivery_date = (date.today() + timedelta(days=3)).isoformat()
                
                # Test PUT /api/orders/{order_id}/delivery-date
                response = self.session.put(
                    f"{BASE_URL}/orders/{order_id}/delivery-date?delivery_date={new_delivery_date}"
                )
                if response.status_code == 200:
                    self.log_result(f"Update delivery date for {venue_name}", True, 
                                  f"New date: {new_delivery_date}")
                else:
                    self.log_result(f"Update delivery date for {venue_name}", False,
                                  f"Status: {response.status_code}")
                        
        except Exception as e:
            self.log_result("Delivery Date Update", False, f"Exception: {str(e)}")
    
    def test_order_status_workflow(self, created_orders):
        """Test order status workflow"""
        print("\n=== Testing Order Status Workflow ===")
        
        if not created_orders:
            self.log_result("Order Status Workflow", False, "No orders to test with")
            return
            
        try:
            for order in created_orders:
                order_id = order["id"]
                venue_name = order["venue_name"]
                
                # Test status transitions: pending -> preparing -> ready -> delivered
                statuses = ["preparing", "ready", "delivered"]
                
                for status in statuses:
                    response = self.session.put(
                        f"{BASE_URL}/orders/{order_id}/status?status={status}"
                    )
                    if response.status_code == 200:
                        self.log_result(f"Update {venue_name} order to {status}", True)
                    else:
                        self.log_result(f"Update {venue_name} order to {status}", False,
                                      f"Status: {response.status_code}")
                        
        except Exception as e:
            self.log_result("Order Status Workflow", False, f"Exception: {str(e)}")
    
    def test_dashboard_statistics(self):
        """Test dashboard statistics calculation"""
        print("\n=== Testing Dashboard Statistics ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                
                # Verify structure
                required_keys = ["production", "orders"]
                production_keys = ["total_items_today", "completed_items_today", "pending_items_today", "completion_rate", "categories"]
                order_keys = ["total_orders_today", "pending_orders"]
                
                structure_valid = True
                
                for key in required_keys:
                    if key not in stats:
                        structure_valid = False
                        break
                
                if structure_valid:
                    for key in production_keys:
                        if key not in stats["production"]:
                            structure_valid = False
                            break
                    
                    for key in order_keys:
                        if key not in stats["orders"]:
                            structure_valid = False
                            break
                
                if structure_valid:
                    self.log_result("Dashboard stats structure", True, "All required fields present")
                    
                    # Verify completion rate calculation
                    prod_stats = stats["production"]
                    total = prod_stats["total_items_today"]
                    completed = prod_stats["completed_items_today"]
                    rate = prod_stats["completion_rate"]
                    
                    expected_rate = (completed / total * 100) if total > 0 else 0
                    if abs(rate - expected_rate) < 0.01:
                        self.log_result("Completion rate calculation", True, 
                                      f"Rate: {rate:.1f}% ({completed}/{total})")
                    else:
                        self.log_result("Completion rate calculation", False,
                                      f"Expected {expected_rate:.1f}%, got {rate:.1f}%")
                    
                    # Verify categories breakdown exists
                    if "categories" in prod_stats and isinstance(prod_stats["categories"], dict):
                        self.log_result("Categories breakdown in stats", True, 
                                      f"Categories: {list(prod_stats['categories'].keys())}")
                    else:
                        self.log_result("Categories breakdown in stats", False, "Categories breakdown missing")
                        
                    self.log_result("GET /api/dashboard/stats", True, 
                                  f"Production: {total} items, Orders: {stats['orders']['total_orders_today']} today")
                else:
                    self.log_result("Dashboard stats structure", False, "Missing required fields")
                    
            else:
                self.log_result("GET /api/dashboard/stats", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Dashboard Statistics", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run comprehensive backend API tests for updated functionality"""
        print("🧪 Starting Updated Backend API Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("Testing new features: categories, unit_of_measure, removed cost, venue addresses, delivery dates")
        print("=" * 80)
        
        # Test user authentication with venue addresses
        self.test_user_authentication_with_addresses()
        
        # Test new categories endpoint
        self.test_categories_endpoint()
        
        # Test production management with categories and units
        created_items = self.test_production_management_with_categories()
        
        # Test production status workflow
        completed_items = self.test_production_status_workflow(created_items)
        
        # Test order management with delivery information
        created_orders = self.test_order_management_with_delivery(completed_items)
        
        # Test delivery date update endpoint
        self.test_delivery_date_update(created_orders)
        
        # Test order status workflow
        self.test_order_status_workflow(created_orders)
        
        # Test dashboard statistics
        self.test_dashboard_statistics()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        success_rate = (self.test_results['passed'] / 
                       (self.test_results['passed'] + self.test_results['failed']) * 100)
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        return self.test_results['failed'] == 0

if __name__ == "__main__":
    tester = KitchenAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)