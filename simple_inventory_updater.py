#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Alibaba.com Inventory Updater

This script focuses only on inventory updates with better error handling
and debugging information.

Usage:
    python3 simple_inventory_updater.py input.csv
"""

import iop
import csv
import sys
import os
import time
import json

# Configuration
APP_KEY = "501504"
ACCESS_TOKEN = "50000202005YOdq5O1d982d9btzFodOHZGQykFZktseKtxSOP0z5pCqa1N38Rr"
APP_SECRET = "VYO05f6i6FCMAlDD6GpT3x3BOdEv6Cqv"
BASE_URL = "https://openapi-api.alibaba.com/rest"
INVENTORY_UPDATE_API = "/icbu/product/edit-inventory"

def test_single_inventory_update(product_id, inventory):
    """Test updating inventory for a single product with detailed debugging"""
    print(f"🔍 Testing inventory update for product {product_id}")
    print("=" * 50)
    
    try:
        # Initialize client
        client = iop.IopClient(BASE_URL, APP_KEY, APP_SECRET)
        
        # Create request
        request = iop.IopRequest(INVENTORY_UPDATE_API, "POST")
        request.set_simplify()
        
        # Add parameters
        request.add_api_param('product_id', product_id)
        request.add_api_param('inventory', str(inventory))
        
        print(f"API Endpoint: {INVENTORY_UPDATE_API}")
        print(f"Product ID: {product_id}")
        print(f"Inventory: {inventory}")
        print(f"App Key: {APP_KEY}")
        print(f"Access Token: {ACCESS_TOKEN[:20]}...")
        
        # Execute request
        print("\nSending request...")
        response = client.execute(request, ACCESS_TOKEN)
        
        print(f"\nResponse Details:")
        print(f"  Code: {response.code}")
        print(f"  Type: {response.type}")
        print(f"  Message: {response.message}")
        print(f"  Request ID: {response.request_id}")
        
        if response.body:
            print(f"  Full Response: {json.dumps(response.body, indent=2)}")
        
        if response.code == "0":
            print("✅ Inventory update successful!")
            return True
        else:
            print(f"❌ Inventory update failed: {response.message}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

def process_csv_file(csv_file_path):
    """Process CSV file and update inventory for each product"""
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return
    
    print(f"📁 Reading CSV file: {csv_file_path}")
    print("=" * 60)
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                product_id = row['Product_id'].strip()
                inventory = int(row['inventory'].strip())
                
                print(f"\n🔄 Processing row {row_num}")
                success = test_single_inventory_update(product_id, inventory)
                
                if not success:
                    print(f"❌ Failed to update product {product_id}")
                else:
                    print(f"✅ Successfully updated product {product_id}")
                
                # Add delay between requests
                if row_num < len(list(csv.DictReader(open(csv_file_path, 'r', encoding='utf-8')))):
                    print("⏳ Waiting 2 seconds before next request...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error processing row {row_num}: {e}")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 simple_inventory_updater.py <csv_file>")
        print("\nCSV Format:")
        print("Product_id,inventory")
        print("1601488259004,10")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("🚀 Simple Alibaba.com Inventory Updater")
    print("=" * 60)
    
    process_csv_file(csv_file)
    
    print("\n✅ Process completed!")

if __name__ == "__main__":
    main()
