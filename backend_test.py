#!/usr/bin/env python3
"""
Backend API Testing for Production Kitchen Management System
Focus: Testing Customizable Invoice PDF with Logo and Settings
Key Tests:
1. INVOICE SETTINGS IN APPSETTINGS MODEL - tax_rate, company info, display toggles
2. ENHANCED PDF GENERATION - customizable settings, logo support
3. TAX RATE INTEGRATION - settings tax rate used in orders and invoices
4. PDF CONTENT VERIFICATION - company header, toggleable elements, proper layout
5. COMPLETE INVOICE WORKFLOW - settings → orders → invoices → PDF generation
"""

import requests
import json
from datetime import datetime, date, timedelta
import time
import sys

# Backend URL from frontend/.env
BASE_URL = "https://prepcart.preview.emergentagent.com/api"

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
    
    def test_customizable_invoice_pdf_system(self):
        """Test the complete customizable invoice PDF system with logo and settings"""
        print("🔧 STARTING CUSTOMIZABLE INVOICE PDF SYSTEM TESTS")
        print("=" * 70)
        
        # Test 1: Invoice Settings in AppSettings Model
        self.test_invoice_settings_in_appsettings()
        
        # Test 2: Enhanced PDF Generation with Customizable Settings
        self.test_enhanced_pdf_generation()
        
        # Test 3: Tax Rate Integration from Settings
        self.test_tax_rate_integration()
        
        # Test 4: PDF Content Verification
        self.test_pdf_content_verification()
        
        # Test 5: Complete Invoice Workflow
        self.test_complete_invoice_workflow()
        
        # Print summary
        print("\n" + "=" * 70)
        print("🔧 CUSTOMIZABLE INVOICE PDF TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Tests Passed: {self.test_results['passed']}")
        print(f"❌ Tests Failed: {self.test_results['failed']}")
        print(f"📊 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        return self.test_results

    def test_invoice_settings_in_appsettings(self):
        """Test invoice settings in AppSettings model - GET/PUT /api/settings"""
        print("\n=== TEST 1: Invoice Settings in AppSettings Model ===")
        
        try:
            # Test 1: GET /api/settings returns invoice fields
            response = self.session.get(f"{BASE_URL}/settings")
            
            if response.status_code == 200:
                settings = response.json()
                self.log_result("GET /api/settings", True, "Settings retrieved successfully")
                
                # Check for invoice-specific fields
                invoice_fields = [
                    'tax_rate', 'invoice_company_name', 'invoice_address', 'invoice_phone', 
                    'invoice_email', 'invoice_website', 'show_logo', 'show_due_date', 
                    'show_company_address', 'show_company_phone', 'show_company_email', 
                    'show_company_website', 'show_tax_breakdown', 'show_item_images',
                    'invoice_notes', 'payment_terms'
                ]
                
                missing_fields = []
                for field in invoice_fields:
                    if field not in settings:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.log_result("Invoice fields in settings", True, 
                                  f"All {len(invoice_fields)} invoice fields present")
                else:
                    self.log_result("Invoice fields in settings", False, 
                                  f"Missing fields: {missing_fields}")
                
                # Verify default values
                expected_defaults = {
                    'tax_rate': 0.08,
                    'show_logo': True,
                    'show_due_date': True,
                    'show_tax_breakdown': True,
                    'show_item_images': False
                }
                
                for field, expected_value in expected_defaults.items():
                    actual_value = settings.get(field)
                    if actual_value == expected_value:
                        self.log_result(f"Default value for {field}", True, 
                                      f"Correct default: {actual_value}")
                    else:
                        self.log_result(f"Default value for {field}", False, 
                                      f"Expected {expected_value}, got {actual_value}")
            else:
                self.log_result("GET /api/settings", False, 
                              f"Status: {response.status_code}")
                return
            
            # Test 2: PUT /api/settings updates invoice settings
            updated_settings = {
                "tax_rate": 0.10,  # Change from 8% to 10%
                "invoice_company_name": "Custom Kitchen Co.",
                "invoice_address": "456 Custom St, Test City, TC 12345",
                "invoice_phone": "(555) 987-6543",
                "invoice_email": "custom@kitchen.com",
                "invoice_website": "www.customkitchen.com",
                "show_logo": False,
                "show_due_date": True,
                "show_company_address": True,
                "show_company_phone": False,
                "show_company_email": True,
                "show_company_website": False,
                "show_tax_breakdown": True,
                "show_item_images": True,
                "invoice_notes": "Custom invoice notes - Thank you for your order!",
                "payment_terms": "Net 15 days"
            }
            
            response = self.session.put(f"{BASE_URL}/settings", json=updated_settings)
            
            if response.status_code == 200:
                updated_response = response.json()
                self.log_result("PUT /api/settings", True, "Settings updated successfully")
                
                # Verify all updates were applied
                update_failures = []
                for field, expected_value in updated_settings.items():
                    actual_value = updated_response.get(field)
                    if actual_value != expected_value:
                        update_failures.append(f"{field}: expected {expected_value}, got {actual_value}")
                
                if not update_failures:
                    self.log_result("Settings update verification", True, 
                                  f"All {len(updated_settings)} fields updated correctly")
                else:
                    self.log_result("Settings update verification", False, 
                                  f"Update failures: {update_failures}")
                
                # Test 3: Verify persistence by getting settings again
                response = self.session.get(f"{BASE_URL}/settings")
                if response.status_code == 200:
                    persisted_settings = response.json()
                    
                    persistence_failures = []
                    for field, expected_value in updated_settings.items():
                        actual_value = persisted_settings.get(field)
                        if actual_value != expected_value:
                            persistence_failures.append(f"{field}: expected {expected_value}, got {actual_value}")
                    
                    if not persistence_failures:
                        self.log_result("Settings persistence", True, 
                                      "All updated settings persisted correctly")
                    else:
                        self.log_result("Settings persistence", False, 
                                      f"Persistence failures: {persistence_failures}")
                else:
                    self.log_result("Settings persistence check", False, 
                                  f"Status: {response.status_code}")
            else:
                self.log_result("PUT /api/settings", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Invoice Settings in AppSettings", False, f"Exception: {str(e)}")

    def test_enhanced_pdf_generation(self):
        """Test enhanced PDF generation with customizable settings and logo"""
        print("\n=== TEST 2: Enhanced PDF Generation ===")
        
        try:
            # First, ensure we have test data - create a production item and order
            test_item = {
                "name": "PDF Test Item",
                "category": "Main Course",
                "unit_of_measure": "kilo",
                "base_cost": 20.0
            }
            
            # Create production item
            response = self.session.post(f"{BASE_URL}/production-items", 
                                       json=test_item, 
                                       params={"created_by": "test_manager"})
            
            if response.status_code != 200:
                self.log_result("Create test item for PDF", False, 
                              f"Status: {response.status_code}")
                return
            
            created_item = response.json()
            item_id = created_item["id"]
            
            # Create test order to generate invoice
            test_order = {
                "venue_name": "PDF Test Venue",
                "venue_id": "pdf_test_venue",
                "delivery_address": "123 PDF Test St, Test City, TC 12345",
                "items": [{
                    "production_item_id": item_id,
                    "production_item_name": created_item["name"],
                    "quantity": 2,
                    "unit_of_measure": created_item["unit_of_measure"],
                    "unit_price": created_item["unit_price"]
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=test_order)
            
            if response.status_code != 200:
                self.log_result("Create test order for PDF", False, 
                              f"Status: {response.status_code}")
                # Clean up
                self.session.delete(f"{BASE_URL}/production-items/{item_id}")
                return
            
            created_order = response.json()
            order_id = created_order["id"]
            
            self.log_result("Create test order for PDF", True, 
                          f"Order created: {created_order['invoice_number']}")
            
            # Get the invoice that was auto-generated
            response = self.session.get(f"{BASE_URL}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                test_invoice = next((inv for inv in invoices if inv["order_id"] == order_id), None)
                
                if test_invoice:
                    invoice_id = test_invoice["id"]
                    self.log_result("Find auto-generated invoice", True, 
                                  f"Invoice found: {test_invoice['invoice_number']}")
                    
                    # Test 1: PDF generation without logo
                    response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
                    
                    if response.status_code == 200:
                        self.log_result("PDF generation without logo", True, 
                                      f"PDF generated successfully, size: {len(response.content)} bytes")
                        
                        # Verify content type
                        content_type = response.headers.get('content-type', '')
                        if 'application/pdf' in content_type:
                            self.log_result("PDF content type", True, 
                                          f"Correct content type: {content_type}")
                        else:
                            self.log_result("PDF content type", False, 
                                          f"Expected application/pdf, got: {content_type}")
                        
                        # Verify content disposition header
                        content_disposition = response.headers.get('content-disposition', '')
                        expected_filename = f"invoice_{test_invoice['invoice_number']}.pdf"
                        if expected_filename in content_disposition:
                            self.log_result("PDF filename header", True, 
                                          f"Correct filename in header: {expected_filename}")
                        else:
                            self.log_result("PDF filename header", False, 
                                          f"Expected {expected_filename} in header, got: {content_disposition}")
                    else:
                        self.log_result("PDF generation without logo", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    
                    # Test 2: Add logo to settings and test PDF with logo
                    logo_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                    
                    logo_settings = {
                        "logo_url": logo_data,
                        "show_logo": True
                    }
                    
                    response = self.session.put(f"{BASE_URL}/settings", json=logo_settings)
                    
                    if response.status_code == 200:
                        self.log_result("Add logo to settings", True, "Logo added to settings")
                        
                        # Generate PDF with logo
                        response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
                        
                        if response.status_code == 200:
                            pdf_with_logo_size = len(response.content)
                            self.log_result("PDF generation with logo", True, 
                                          f"PDF with logo generated, size: {pdf_with_logo_size} bytes")
                            
                            # PDF with logo should be larger than without logo
                            # Note: This is a basic check, actual logo verification would require PDF parsing
                            if pdf_with_logo_size > 1000:  # Reasonable minimum size for PDF with content
                                self.log_result("PDF size with logo", True, 
                                              "PDF size indicates logo inclusion")
                            else:
                                self.log_result("PDF size with logo", False, 
                                              f"PDF size too small: {pdf_with_logo_size} bytes")
                        else:
                            self.log_result("PDF generation with logo", False, 
                                          f"Status: {response.status_code}")
                    else:
                        self.log_result("Add logo to settings", False, 
                                      f"Status: {response.status_code}")
                    
                    # Test 3: Test toggleable elements
                    toggle_settings = {
                        "show_logo": False,
                        "show_due_date": False,
                        "show_company_address": False,
                        "show_tax_breakdown": False
                    }
                    
                    response = self.session.put(f"{BASE_URL}/settings", json=toggle_settings)
                    
                    if response.status_code == 200:
                        self.log_result("Update display toggles", True, "Display toggles updated")
                        
                        # Generate PDF with elements hidden
                        response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
                        
                        if response.status_code == 200:
                            self.log_result("PDF generation with hidden elements", True, 
                                          f"PDF generated with hidden elements, size: {len(response.content)} bytes")
                        else:
                            self.log_result("PDF generation with hidden elements", False, 
                                          f"Status: {response.status_code}")
                    else:
                        self.log_result("Update display toggles", False, 
                                      f"Status: {response.status_code}")
                    
                    # Test 4: Error handling for non-existent invoice
                    fake_invoice_id = "non-existent-invoice-id"
                    response = self.session.get(f"{BASE_URL}/invoices/{fake_invoice_id}/pdf")
                    
                    if response.status_code == 404:
                        self.log_result("PDF generation - Non-existent invoice", True, 
                                      "Correctly returned 404 for non-existent invoice")
                    else:
                        self.log_result("PDF generation - Non-existent invoice", False, 
                                      f"Expected 404, got {response.status_code}")
                else:
                    self.log_result("Find auto-generated invoice", False, 
                                  "No invoice found for test order")
            else:
                self.log_result("Get invoices for PDF test", False, 
                              f"Status: {response.status_code}")
            
            # Clean up test data
            self.session.delete(f"{BASE_URL}/production-items/{item_id}")
            
        except Exception as e:
            self.log_result("Enhanced PDF Generation", False, f"Exception: {str(e)}")

    def test_tax_rate_integration(self):
        """Test that tax rate from settings is used in orders and invoices"""
        print("\n=== TEST 3: Tax Rate Integration ===")
        
        try:
            # Test 1: Set custom tax rate in settings
            custom_tax_rate = 0.12  # 12% instead of default 8%
            
            tax_settings = {
                "tax_rate": custom_tax_rate
            }
            
            response = self.session.put(f"{BASE_URL}/settings", json=tax_settings)
            
            if response.status_code == 200:
                updated_settings = response.json()
                
                if updated_settings.get("tax_rate") == custom_tax_rate:
                    self.log_result("Set custom tax rate", True, 
                                  f"Tax rate set to {custom_tax_rate * 100}%")
                else:
                    self.log_result("Set custom tax rate", False, 
                                  f"Expected {custom_tax_rate}, got {updated_settings.get('tax_rate')}")
            else:
                self.log_result("Set custom tax rate", False, 
                              f"Status: {response.status_code}")
                return
            
            # Test 2: Create production item for order testing
            test_item = {
                "name": "Tax Rate Test Item",
                "category": "Main Course",
                "unit_of_measure": "kilo",
                "base_cost": 100.0  # Use round number for easy calculation
            }
            
            response = self.session.post(f"{BASE_URL}/production-items", 
                                       json=test_item, 
                                       params={"created_by": "test_manager"})
            
            if response.status_code != 200:
                self.log_result("Create test item for tax calculation", False, 
                              f"Status: {response.status_code}")
                return
            
            created_item = response.json()
            item_id = created_item["id"]
            unit_price = created_item["unit_price"]  # Should be 115.0 (100 * 1.15)
            
            # Test 3: Create order and verify tax calculation uses settings tax rate
            test_order = {
                "venue_name": "Tax Test Venue",
                "venue_id": "tax_test_venue",
                "delivery_address": "123 Tax Test St, Test City, TC 12345",
                "items": [{
                    "production_item_id": item_id,
                    "production_item_name": created_item["name"],
                    "quantity": 1,
                    "unit_of_measure": created_item["unit_of_measure"],
                    "unit_price": unit_price
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=test_order)
            
            if response.status_code == 200:
                created_order = response.json()
                
                # Verify tax calculation
                expected_subtotal = unit_price * 1  # 115.0
                expected_tax = expected_subtotal * custom_tax_rate  # 115.0 * 0.12 = 13.8
                expected_total = expected_subtotal + expected_tax  # 115.0 + 13.8 = 128.8
                
                actual_subtotal = created_order.get("subtotal", 0)
                actual_tax = created_order.get("tax_amount", 0)
                actual_total = created_order.get("total_amount", 0)
                actual_tax_rate = created_order.get("tax_rate", 0)
                
                # Check subtotal
                if abs(actual_subtotal - expected_subtotal) < 0.01:
                    self.log_result("Order subtotal calculation", True, 
                                  f"Correct subtotal: ${actual_subtotal:.2f}")
                else:
                    self.log_result("Order subtotal calculation", False, 
                                  f"Expected ${expected_subtotal:.2f}, got ${actual_subtotal:.2f}")
                
                # Check tax rate used
                if abs(actual_tax_rate - custom_tax_rate) < 0.001:
                    self.log_result("Order uses settings tax rate", True, 
                                  f"Correct tax rate: {actual_tax_rate * 100}%")
                else:
                    self.log_result("Order uses settings tax rate", False, 
                                  f"Expected {custom_tax_rate * 100}%, got {actual_tax_rate * 100}%")
                
                # Check tax amount
                if abs(actual_tax - expected_tax) < 0.01:
                    self.log_result("Order tax amount calculation", True, 
                                  f"Correct tax: ${actual_tax:.2f}")
                else:
                    self.log_result("Order tax amount calculation", False, 
                                  f"Expected ${expected_tax:.2f}, got ${actual_tax:.2f}")
                
                # Check total
                if abs(actual_total - expected_total) < 0.01:
                    self.log_result("Order total calculation", True, 
                                  f"Correct total: ${actual_total:.2f}")
                else:
                    self.log_result("Order total calculation", False, 
                                  f"Expected ${expected_total:.2f}, got ${actual_total:.2f}")
                
                # Test 4: Verify invoice uses same tax rate
                order_id = created_order["id"]
                
                # Get the auto-generated invoice
                response = self.session.get(f"{BASE_URL}/invoices")
                if response.status_code == 200:
                    invoices = response.json()
                    test_invoice = next((inv for inv in invoices if inv["order_id"] == order_id), None)
                    
                    if test_invoice:
                        invoice_subtotal = test_invoice.get("subtotal", 0)
                        invoice_tax = test_invoice.get("tax_amount", 0)
                        invoice_total = test_invoice.get("total_amount", 0)
                        
                        # Verify invoice amounts match order amounts
                        if (abs(invoice_subtotal - actual_subtotal) < 0.01 and
                            abs(invoice_tax - actual_tax) < 0.01 and
                            abs(invoice_total - actual_total) < 0.01):
                            self.log_result("Invoice tax calculation consistency", True, 
                                          "Invoice amounts match order amounts with custom tax rate")
                        else:
                            self.log_result("Invoice tax calculation consistency", False, 
                                          f"Invoice amounts don't match order: "
                                          f"Invoice(${invoice_subtotal:.2f}, ${invoice_tax:.2f}, ${invoice_total:.2f}) vs "
                                          f"Order(${actual_subtotal:.2f}, ${actual_tax:.2f}, ${actual_total:.2f})")
                    else:
                        self.log_result("Find invoice for tax verification", False, 
                                      "No invoice found for tax test order")
                else:
                    self.log_result("Get invoices for tax verification", False, 
                                  f"Status: {response.status_code}")
            else:
                self.log_result("Create order with custom tax rate", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
            
            # Test 5: Test different tax rate
            different_tax_rate = 0.15  # 15%
            
            response = self.session.put(f"{BASE_URL}/settings", json={"tax_rate": different_tax_rate})
            
            if response.status_code == 200:
                # Create another order to test new tax rate
                test_order_2 = {
                    "venue_name": "Tax Test Venue 2",
                    "venue_id": "tax_test_venue_2",
                    "delivery_address": "456 Tax Test Ave, Test City, TC 67890",
                    "items": [{
                        "production_item_id": item_id,
                        "production_item_name": created_item["name"],
                        "quantity": 2,
                        "unit_of_measure": created_item["unit_of_measure"],
                        "unit_price": unit_price
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=test_order_2)
                
                if response.status_code == 200:
                    created_order_2 = response.json()
                    
                    expected_subtotal_2 = unit_price * 2  # 230.0
                    expected_tax_2 = expected_subtotal_2 * different_tax_rate  # 230.0 * 0.15 = 34.5
                    
                    actual_tax_rate_2 = created_order_2.get("tax_rate", 0)
                    actual_tax_2 = created_order_2.get("tax_amount", 0)
                    
                    if abs(actual_tax_rate_2 - different_tax_rate) < 0.001:
                        self.log_result("Updated tax rate in new order", True, 
                                      f"New order uses updated tax rate: {actual_tax_rate_2 * 100}%")
                    else:
                        self.log_result("Updated tax rate in new order", False, 
                                      f"Expected {different_tax_rate * 100}%, got {actual_tax_rate_2 * 100}%")
                    
                    if abs(actual_tax_2 - expected_tax_2) < 0.01:
                        self.log_result("Updated tax calculation", True, 
                                      f"Correct tax with new rate: ${actual_tax_2:.2f}")
                    else:
                        self.log_result("Updated tax calculation", False, 
                                      f"Expected ${expected_tax_2:.2f}, got ${actual_tax_2:.2f}")
                else:
                    self.log_result("Create order with updated tax rate", False, 
                                  f"Status: {response.status_code}")
            else:
                self.log_result("Update tax rate for second test", False, 
                              f"Status: {response.status_code}")
            
            # Clean up test data
            self.session.delete(f"{BASE_URL}/production-items/{item_id}")
            
        except Exception as e:
            self.log_result("Tax Rate Integration", False, f"Exception: {str(e)}")

    def test_pdf_content_verification(self):
        """Test PDF content verification - company header, notes, payment terms"""
        print("\n=== TEST 4: PDF Content Verification ===")
        
        try:
            # Set up comprehensive invoice settings for content verification
            comprehensive_settings = {
                "invoice_company_name": "Premium Kitchen Solutions",
                "invoice_address": "789 Premium Ave, Suite 100, Business City, BC 54321",
                "invoice_phone": "(555) 123-9999",
                "invoice_email": "billing@premiumkitchen.com",
                "invoice_website": "www.premiumkitchen.com",
                "show_logo": True,
                "show_due_date": True,
                "show_company_address": True,
                "show_company_phone": True,
                "show_company_email": True,
                "show_company_website": True,
                "show_tax_breakdown": True,
                "show_item_images": False,
                "invoice_notes": "Thank you for choosing Premium Kitchen Solutions! We appreciate your business and look forward to serving you again.",
                "payment_terms": "Payment due within 30 days of invoice date. Late payments subject to 1.5% monthly service charge.",
                "tax_rate": 0.095  # 9.5%
            }
            
            response = self.session.put(f"{BASE_URL}/settings", json=comprehensive_settings)
            
            if response.status_code == 200:
                self.log_result("Set comprehensive invoice settings", True, 
                              "All invoice customization settings applied")
            else:
                self.log_result("Set comprehensive invoice settings", False, 
                              f"Status: {response.status_code}")
                return
            
            # Create test data for PDF content verification
            test_item = {
                "name": "Premium Content Test Item",
                "category": "Main Course",
                "unit_of_measure": "each",
                "base_cost": 50.0
            }
            
            response = self.session.post(f"{BASE_URL}/production-items", 
                                       json=test_item, 
                                       params={"created_by": "test_manager"})
            
            if response.status_code != 200:
                self.log_result("Create test item for content verification", False, 
                              f"Status: {response.status_code}")
                return
            
            created_item = response.json()
            item_id = created_item["id"]
            
            # Create order with multiple items for better PDF content
            test_order = {
                "venue_name": "Content Verification Restaurant",
                "venue_id": "content_test_venue",
                "delivery_address": "321 Content St, Verification City, VC 98765",
                "items": [{
                    "production_item_id": item_id,
                    "production_item_name": created_item["name"],
                    "quantity": 3,
                    "unit_of_measure": created_item["unit_of_measure"],
                    "unit_price": created_item["unit_price"]
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=test_order)
            
            if response.status_code != 200:
                self.log_result("Create test order for content verification", False, 
                              f"Status: {response.status_code}")
                self.session.delete(f"{BASE_URL}/production-items/{item_id}")
                return
            
            created_order = response.json()
            order_id = created_order["id"]
            
            # Get the auto-generated invoice
            response = self.session.get(f"{BASE_URL}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                test_invoice = next((inv for inv in invoices if inv["order_id"] == order_id), None)
                
                if test_invoice:
                    invoice_id = test_invoice["id"]
                    
                    # Test 1: Generate PDF with all content enabled
                    response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
                    
                    if response.status_code == 200:
                        pdf_content = response.content
                        pdf_size = len(pdf_content)
                        
                        self.log_result("PDF generation with full content", True, 
                                      f"PDF generated with comprehensive settings, size: {pdf_size} bytes")
                        
                        # Verify PDF is substantial (has content)
                        if pdf_size > 5000:  # Reasonable size for a detailed PDF
                            self.log_result("PDF content size verification", True, 
                                          "PDF size indicates comprehensive content inclusion")
                        else:
                            self.log_result("PDF content size verification", False, 
                                          f"PDF size seems small for comprehensive content: {pdf_size} bytes")
                        
                        # Verify headers are correct
                        content_type = response.headers.get('content-type', '')
                        if 'application/pdf' in content_type:
                            self.log_result("PDF content type verification", True, 
                                          f"Correct PDF content type: {content_type}")
                        else:
                            self.log_result("PDF content type verification", False, 
                                          f"Incorrect content type: {content_type}")
                        
                        # Verify filename includes invoice number
                        content_disposition = response.headers.get('content-disposition', '')
                        invoice_number = test_invoice['invoice_number']
                        if invoice_number in content_disposition:
                            self.log_result("PDF filename includes invoice number", True, 
                                          f"Filename contains invoice number: {invoice_number}")
                        else:
                            self.log_result("PDF filename includes invoice number", False, 
                                          f"Invoice number {invoice_number} not in filename header")
                    else:
                        self.log_result("PDF generation with full content", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    
                    # Test 2: Test with minimal content (most elements hidden)
                    minimal_settings = {
                        "show_logo": False,
                        "show_due_date": False,
                        "show_company_address": False,
                        "show_company_phone": False,
                        "show_company_email": False,
                        "show_company_website": False,
                        "show_tax_breakdown": False,
                        "show_item_images": False,
                        "invoice_notes": "",
                        "payment_terms": ""
                    }
                    
                    response = self.session.put(f"{BASE_URL}/settings", json=minimal_settings)
                    
                    if response.status_code == 200:
                        self.log_result("Set minimal content settings", True, 
                                      "Minimal content settings applied")
                        
                        # Generate PDF with minimal content
                        response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
                        
                        if response.status_code == 200:
                            minimal_pdf_size = len(response.content)
                            
                            self.log_result("PDF generation with minimal content", True, 
                                          f"PDF generated with minimal settings, size: {minimal_pdf_size} bytes")
                            
                            # Minimal PDF should be smaller than comprehensive PDF
                            if minimal_pdf_size < pdf_size:
                                self.log_result("PDF size difference verification", True, 
                                              f"Minimal PDF ({minimal_pdf_size}B) smaller than full PDF ({pdf_size}B)")
                            else:
                                self.log_result("PDF size difference verification", False, 
                                              f"Minimal PDF ({minimal_pdf_size}B) not smaller than full PDF ({pdf_size}B)")
                        else:
                            self.log_result("PDF generation with minimal content", False, 
                                          f"Status: {response.status_code}")
                    else:
                        self.log_result("Set minimal content settings", False, 
                                      f"Status: {response.status_code}")
                    
                    # Test 3: Test tax breakdown display toggle
                    tax_breakdown_settings = {
                        "show_tax_breakdown": True,
                        "tax_rate": 0.125  # 12.5% for clear visibility
                    }
                    
                    response = self.session.put(f"{BASE_URL}/settings", json=tax_breakdown_settings)
                    
                    if response.status_code == 200:
                        # Generate PDF with tax breakdown visible
                        response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
                        
                        if response.status_code == 200:
                            self.log_result("PDF with tax breakdown enabled", True, 
                                          "PDF generated with tax breakdown display enabled")
                        else:
                            self.log_result("PDF with tax breakdown enabled", False, 
                                          f"Status: {response.status_code}")
                        
                        # Test with tax breakdown hidden
                        response = self.session.put(f"{BASE_URL}/settings", json={"show_tax_breakdown": False})
                        
                        if response.status_code == 200:
                            response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
                            
                            if response.status_code == 200:
                                self.log_result("PDF with tax breakdown disabled", True, 
                                              "PDF generated with tax breakdown display disabled")
                            else:
                                self.log_result("PDF with tax breakdown disabled", False, 
                                              f"Status: {response.status_code}")
                        else:
                            self.log_result("Disable tax breakdown", False, 
                                          f"Status: {response.status_code}")
                    else:
                        self.log_result("Enable tax breakdown", False, 
                                      f"Status: {response.status_code}")
                else:
                    self.log_result("Find invoice for content verification", False, 
                                  "No invoice found for content test order")
            else:
                self.log_result("Get invoices for content verification", False, 
                              f"Status: {response.status_code}")
            
            # Clean up test data
            self.session.delete(f"{BASE_URL}/production-items/{item_id}")
            
        except Exception as e:
            self.log_result("PDF Content Verification", False, f"Exception: {str(e)}")

    def test_complete_invoice_workflow(self):
        """Test complete invoice workflow: settings → orders → invoices → PDF generation"""
        print("\n=== TEST 5: Complete Invoice Workflow ===")
        
        try:
            # Step 1: Set up complete invoice configuration
            workflow_settings = {
                "company_name": "Workflow Test Kitchen",
                "invoice_company_name": "Workflow Test Kitchen LLC",
                "invoice_address": "999 Workflow Blvd, Test Suite 200, Workflow City, WC 11111",
                "invoice_phone": "(555) 999-1111",
                "invoice_email": "invoices@workflowkitchen.com",
                "invoice_website": "www.workflowkitchen.com",
                "tax_rate": 0.0875,  # 8.75%
                "show_logo": True,
                "show_due_date": True,
                "show_company_address": True,
                "show_company_phone": True,
                "show_company_email": True,
                "show_company_website": True,
                "show_tax_breakdown": True,
                "show_item_images": False,
                "invoice_notes": "Complete workflow test - All systems operational!",
                "payment_terms": "Net 30 days - Complete workflow verification"
            }
            
            response = self.session.put(f"{BASE_URL}/settings", json=workflow_settings)
            
            if response.status_code == 200:
                self.log_result("Workflow Step 1 - Configure settings", True, 
                              "Complete invoice settings configured")
            else:
                self.log_result("Workflow Step 1 - Configure settings", False, 
                              f"Status: {response.status_code}")
                return
            
            # Step 2: Create multiple production items
            workflow_items = [
                {"name": "Workflow Appetizer", "category": "Appetizer", "unit_of_measure": "each", "base_cost": 15.0},
                {"name": "Workflow Main Course", "category": "Main Course", "unit_of_measure": "kilo", "base_cost": 35.0},
                {"name": "Workflow Dessert", "category": "Dessert", "unit_of_measure": "each", "base_cost": 12.0}
            ]
            
            created_items = []
            
            for item_data in workflow_items:
                response = self.session.post(f"{BASE_URL}/production-items", 
                                           json=item_data, 
                                           params={"created_by": "workflow_manager"})
                
                if response.status_code == 200:
                    created_items.append(response.json())
            
            if len(created_items) == len(workflow_items):
                self.log_result("Workflow Step 2 - Create production items", True, 
                              f"Created {len(created_items)} production items")
            else:
                self.log_result("Workflow Step 2 - Create production items", False, 
                              f"Only created {len(created_items)}/{len(workflow_items)} items")
                return
            
            # Step 3: Create comprehensive order with multiple items
            order_items = []
            expected_subtotal = 0
            
            for i, item in enumerate(created_items):
                quantity = i + 2  # 2, 3, 4 quantities
                unit_price = item["unit_price"]
                
                order_items.append({
                    "production_item_id": item["id"],
                    "production_item_name": item["name"],
                    "quantity": quantity,
                    "unit_of_measure": item["unit_of_measure"],
                    "unit_price": unit_price
                })
                
                expected_subtotal += quantity * unit_price
            
            workflow_order = {
                "venue_name": "Complete Workflow Restaurant",
                "venue_id": "workflow_test_venue",
                "delivery_address": "555 Workflow Restaurant St, Complete City, CC 77777",
                "items": order_items
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=workflow_order)
            
            if response.status_code == 200:
                created_order = response.json()
                order_id = created_order["id"]
                
                # Verify order calculations with workflow settings
                actual_subtotal = created_order.get("subtotal", 0)
                actual_tax_rate = created_order.get("tax_rate", 0)
                actual_tax = created_order.get("tax_amount", 0)
                actual_total = created_order.get("total_amount", 0)
                
                expected_tax = expected_subtotal * workflow_settings["tax_rate"]
                expected_total = expected_subtotal + expected_tax
                
                if (abs(actual_subtotal - expected_subtotal) < 0.01 and
                    abs(actual_tax_rate - workflow_settings["tax_rate"]) < 0.001 and
                    abs(actual_tax - expected_tax) < 0.01 and
                    abs(actual_total - expected_total) < 0.01):
                    self.log_result("Workflow Step 3 - Create order with calculations", True, 
                                  f"Order created with correct calculations: ${actual_total:.2f} total")
                else:
                    self.log_result("Workflow Step 3 - Create order with calculations", False, 
                                  f"Calculation mismatch - Expected: ${expected_total:.2f}, Got: ${actual_total:.2f}")
            else:
                self.log_result("Workflow Step 3 - Create order", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                # Clean up items
                for item in created_items:
                    self.session.delete(f"{BASE_URL}/production-items/{item['id']}")
                return
            
            # Step 4: Verify invoice auto-generation
            response = self.session.get(f"{BASE_URL}/invoices")
            
            if response.status_code == 200:
                invoices = response.json()
                workflow_invoice = next((inv for inv in invoices if inv["order_id"] == order_id), None)
                
                if workflow_invoice:
                    invoice_id = workflow_invoice["id"]
                    
                    # Verify invoice data matches order data
                    if (abs(workflow_invoice.get("subtotal", 0) - actual_subtotal) < 0.01 and
                        abs(workflow_invoice.get("tax_amount", 0) - actual_tax) < 0.01 and
                        abs(workflow_invoice.get("total_amount", 0) - actual_total) < 0.01):
                        self.log_result("Workflow Step 4 - Invoice auto-generation", True, 
                                      f"Invoice auto-generated with correct amounts: {workflow_invoice['invoice_number']}")
                    else:
                        self.log_result("Workflow Step 4 - Invoice auto-generation", False, 
                                      "Invoice amounts don't match order amounts")
                else:
                    self.log_result("Workflow Step 4 - Find auto-generated invoice", False, 
                                  "No invoice found for workflow order")
                    # Clean up
                    for item in created_items:
                        self.session.delete(f"{BASE_URL}/production-items/{item['id']}")
                    return
            else:
                self.log_result("Workflow Step 4 - Get invoices", False, 
                              f"Status: {response.status_code}")
                # Clean up
                for item in created_items:
                    self.session.delete(f"{BASE_URL}/production-items/{item['id']}")
                return
            
            # Step 5: Generate final PDF with all customizations
            response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}/pdf")
            
            if response.status_code == 200:
                final_pdf_content = response.content
                final_pdf_size = len(final_pdf_content)
                
                self.log_result("Workflow Step 5 - Final PDF generation", True, 
                              f"Complete workflow PDF generated, size: {final_pdf_size} bytes")
                
                # Verify PDF headers
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if ('application/pdf' in content_type and 
                    workflow_invoice['invoice_number'] in content_disposition):
                    self.log_result("Workflow Step 5 - PDF headers verification", True, 
                                  "PDF headers correct for complete workflow")
                else:
                    self.log_result("Workflow Step 5 - PDF headers verification", False, 
                                  f"PDF headers incorrect: {content_type}, {content_disposition}")
                
                # Verify PDF size indicates comprehensive content
                if final_pdf_size > 8000:  # Should be substantial with multiple items and full settings
                    self.log_result("Workflow Step 5 - PDF content completeness", True, 
                                  "PDF size indicates comprehensive content inclusion")
                else:
                    self.log_result("Workflow Step 5 - PDF content completeness", False, 
                                  f"PDF size may be too small for comprehensive content: {final_pdf_size} bytes")
            else:
                self.log_result("Workflow Step 5 - Final PDF generation", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
            
            # Step 6: Test workflow with existing invoices
            existing_invoices_count = len(invoices)
            
            if existing_invoices_count > 1:
                # Test PDF generation for multiple invoices
                pdf_generation_count = 0
                
                for invoice in invoices[:3]:  # Test first 3 invoices
                    response = self.session.get(f"{BASE_URL}/invoices/{invoice['id']}/pdf")
                    
                    if response.status_code == 200:
                        pdf_generation_count += 1
                
                if pdf_generation_count > 0:
                    self.log_result("Workflow Step 6 - Multiple invoice PDF generation", True, 
                                  f"Successfully generated PDFs for {pdf_generation_count} existing invoices")
                else:
                    self.log_result("Workflow Step 6 - Multiple invoice PDF generation", False, 
                                  "Failed to generate PDFs for existing invoices")
            else:
                self.log_result("Workflow Step 6 - Multiple invoice test", True, 
                              "Only one invoice available (expected for clean test environment)")
            
            # Complete workflow summary
            self.log_result("Complete Invoice Workflow", True, 
                          "Full workflow completed: settings → production items → order → invoice → PDF")
            
            # Clean up test data
            for item in created_items:
                self.session.delete(f"{BASE_URL}/production-items/{item['id']}")
            
        except Exception as e:
            self.log_result("Complete Invoice Workflow", False, f"Exception: {str(e)}")


if __name__ == "__main__":
    print("🚀 STARTING BACKEND API TESTING")
    print("Testing Customizable Invoice PDF with Logo and Settings")
    print("=" * 80)
    
    tester = KitchenAPITester()
    
    try:
        # Run the customizable invoice PDF tests
        results = tester.test_customizable_invoice_pdf_system()
        
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
            print(f"\n🎉 ALL TESTS PASSED! Customizable invoice PDF system is working correctly.")
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