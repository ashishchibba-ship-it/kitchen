#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Production Kitchen Management System
Tests all endpoints and business logic including 15% markup calculation and status workflows
"""

import requests
import json
from datetime import datetime, date
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
    
    def test_user_authentication(self):
        """Test user authentication endpoints and predefined users"""
        print("\n=== Testing User Authentication ===")
        
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
                
                found_users = {user["username"]: user["role"] for user in users}
                
                for username, expected_role in expected_users.items():
                    if username in found_users:
                        if found_users[username] == expected_role:
                            self.log_result(f"User {username} role verification", True, f"Role: {expected_role}")
                        else:
                            self.log_result(f"User {username} role verification", False, 
                                          f"Expected {expected_role}, got {found_users[username]}")
                    else:
                        self.log_result(f"User {username} existence", False, "User not found")
                
                # Test GET /api/users/{username}
                test_username = "manager"
                response = self.session.get(f"{BASE_URL}/users/{test_username}")
                if response.status_code == 200:
                    user = response.json()
                    if user["username"] == test_username and user["role"] == "manager":
                        self.log_result("GET /api/users/{username}", True, f"Retrieved user {test_username}")
                    else:
                        self.log_result("GET /api/users/{username}", False, "User data mismatch")
                else:
                    self.log_result("GET /api/users/{username}", False, f"Status: {response.status_code}")
                    
            else:
                self.log_result("GET /api/users", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("User Authentication", False, f"Exception: {str(e)}")
    
    def test_production_management(self):
        """Test production item management endpoints"""
        print("\n=== Testing Production Management ===")
        
        try:
            # Create test production items
            today = date.today().isoformat()
            
            production_items = [
                {
                    "name": "Fresh Pasta Marinara",
                    "quantity": 50,
                    "target_time": "10:00",
                    "production_date": today,
                    "cost": 8.50,
                    "assigned_staff": "chef_alice"
                },
                {
                    "name": "Grilled Chicken Caesar Salad", 
                    "quantity": 30,
                    "target_time": "11:30",
                    "production_date": today,
                    "cost": 12.75,
                    "assigned_staff": "chef_bob"
                }
            ]
            
            created_items = []
            
            # Test POST /api/production-items
            for item_data in production_items:
                response = self.session.post(
                    f"{BASE_URL}/production-items?created_by=manager",
                    json=item_data
                )
                if response.status_code == 200:
                    item = response.json()
                    created_items.append(item)
                    self.log_result(f"Create production item: {item_data['name']}", True, 
                                  f"ID: {item['id']}")
                else:
                    self.log_result(f"Create production item: {item_data['name']}", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
            
            # Test GET /api/production-items
            response = self.session.get(f"{BASE_URL}/production-items")
            if response.status_code == 200:
                items = response.json()
                self.log_result("GET /api/production-items", True, f"Retrieved {len(items)} items")
                
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
            self.log_result("Production Management", False, f"Exception: {str(e)}")
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
                    f"{BASE_URL}/production-items/{item_id}/status",
                    json="in_progress",
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    self.log_result(f"Update {item_name} to in_progress", True)
                else:
                    self.log_result(f"Update {item_name} to in_progress", False, 
                                  f"Status: {response.status_code}")
                
                # Test status transition: in_progress -> completed
                response = self.session.put(
                    f"{BASE_URL}/production-items/{item_id}/status",
                    json="completed",
                    headers={"Content-Type": "application/json"}
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
    
    def test_order_management(self, completed_items):
        """Test inter-venue ordering system with 15% markup"""
        print("\n=== Testing Order Management ===")
        
        if not completed_items:
            self.log_result("Order Management", False, "No completed items to order")
            return []
            
        try:
            # Create test orders
            orders_data = [
                {
                    "venue_name": "Downtown Cafe",
                    "items": [
                        {
                            "production_item_id": completed_items[0]["id"],
                            "production_item_name": completed_items[0]["name"],
                            "quantity": 10,
                            "unit_cost": completed_items[0]["cost"]
                        }
                    ]
                }
            ]
            
            if len(completed_items) > 1:
                orders_data.append({
                    "venue_name": "Uptown Restaurant",
                    "items": [
                        {
                            "production_item_id": completed_items[1]["id"],
                            "production_item_name": completed_items[1]["name"],
                            "quantity": 15,
                            "unit_cost": completed_items[1]["cost"]
                        }
                    ]
                })
            
            created_orders = []
            
            # Test POST /api/orders with 15% markup calculation
            for order_data in orders_data:
                expected_total = sum(item["quantity"] * item["unit_cost"] for item in order_data["items"])
                expected_final = expected_total * 1.15  # 15% markup
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    created_orders.append(order)
                    
                    # Verify 15% markup calculation
                    if abs(order["total_cost"] - expected_total) < 0.01:
                        self.log_result(f"Order total calculation for {order_data['venue_name']}", True,
                                      f"Total: ${order['total_cost']:.2f}")
                    else:
                        self.log_result(f"Order total calculation for {order_data['venue_name']}", False,
                                      f"Expected ${expected_total:.2f}, got ${order['total_cost']:.2f}")
                    
                    if abs(order["final_cost"] - expected_final) < 0.01 and order["markup"] == 15.0:
                        self.log_result(f"15% markup calculation for {order_data['venue_name']}", True,
                                      f"Final: ${order['final_cost']:.2f} (15% markup)")
                    else:
                        self.log_result(f"15% markup calculation for {order_data['venue_name']}", False,
                                      f"Expected ${expected_final:.2f}, got ${order['final_cost']:.2f}")
                        
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
            self.log_result("Order Management", False, f"Exception: {str(e)}")
            return []
    
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
                        f"{BASE_URL}/orders/{order_id}/status",
                        params={"status": status}
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
                production_keys = ["total_items_today", "completed_items_today", "pending_items_today", "completion_rate"]
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
                        
                    self.log_result("GET /api/dashboard/stats", True, 
                                  f"Production: {total} items, Orders: {stats['orders']['total_orders_today']} today")
                else:
                    self.log_result("Dashboard stats structure", False, "Missing required fields")
                    
            else:
                self.log_result("GET /api/dashboard/stats", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Dashboard Statistics", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run comprehensive backend API tests"""
        print("🧪 Starting Comprehensive Backend API Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("=" * 60)
        
        # Test user authentication
        self.test_user_authentication()
        
        # Test production management
        created_items = self.test_production_management()
        
        # Test production status workflow
        completed_items = self.test_production_status_workflow(created_items)
        
        # Test order management with 15% markup
        created_orders = self.test_order_management(completed_items)
        
        # Test order status workflow
        self.test_order_status_workflow(created_orders)
        
        # Test dashboard statistics
        self.test_dashboard_statistics()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
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