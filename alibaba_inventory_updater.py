#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alibaba.com Product Inventory Updater with VLookup

This script reads product data from sample_product_updates.csv and performs
a vlookup against product_skus_ultra_fast.csv to determine the correct inventory structure.

CSV Format (sample_product_updates.csv):
SPU_ID,price,inventory
8718696170731,96,500
5025155028100,600,200

Usage:
    python3 alibaba_inventory_updater.py
"""

import iop
import csv
import sys
import os
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
APP_KEY = os.getenv('APP_KEY', 'your_app_key_here')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', 'your_access_token_here')
APP_SECRET = os.getenv('APP_SECRET', 'your_app_secret_here')
BASE_URL = os.getenv('BASE_URL', 'https://openapi-api.alibaba.com/rest')
INVENTORY_UPDATE_API = "/icbu/product/edit-inventory"
REQUEST_DELAY = 0  # No delay for high-speed processing
MAX_RETRIES = 3
BATCH_SIZE = 50  # Process in batches for better performance

# File paths
SAMPLE_CSV = "sample_product_updates.csv"
SKU_LOOKUP_CSV = "product_skus_ultra_fast.csv"

class AlibabaInventoryUpdater:
    def __init__(self, app_key: str, app_secret: str, access_token: str):
        """Initialize the Alibaba.com API client"""
        self.client = iop.IopClient(BASE_URL, app_key, app_secret)
        self.access_token = access_token
        self.results = []
        self.sku_lookup = {}  # Dictionary to store SPU_ID -> SKU data mapping
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'inventory_updates': 0,
            'sku_inventory_updates': 0,
            'direct_inventory_updates': 0
        }
        self.stats_lock = threading.Lock()  # Thread-safe statistics
        self.processed_count = 0
        self.total_count = 0
        self.start_time = None
    
    def update_stats(self, key: str, increment: int = 1):
        """Thread-safe statistics update"""
        with self.stats_lock:
            self.stats[key] += increment
    
    def update_progress(self, increment: int = 1):
        """Update progress counter"""
        self.processed_count += increment
    
    def load_sku_lookup(self, sku_csv_path: str):
        """Load SKU lookup data from CSV file"""
        print(f"📁 Loading SKU lookup data from: {sku_csv_path}")
        
        if not os.path.exists(sku_csv_path):
            raise FileNotFoundError(f"SKU lookup CSV file not found: {sku_csv_path}")
        
        with open(sku_csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                spu_id = row['SPU_ID'].strip()
                product_id = row['Product_ID'].strip()
                sku_ids_str = row['SKU_IDs'].strip()
                
                # Parse SKU IDs if they exist
                sku_ids = []
                if sku_ids_str:
                    sku_ids = [sku_id.strip() for sku_id in sku_ids_str.split(',') if sku_id.strip()]
                
                self.sku_lookup[spu_id] = {
                    'product_id': product_id,
                    'sku_ids': sku_ids,
                    'has_skus': len(sku_ids) > 0
                }
        
        print(f"✅ Loaded {len(self.sku_lookup)} SPU_ID mappings")
    
    def get_product_info(self, spu_id: str) -> Optional[Dict]:
        """Get product information for a given SPU_ID"""
        return self.sku_lookup.get(spu_id)
    
    def update_sku_inventory(self, product_id: str, sku_ids: List[str], inventory: str, retry_count: int = 0) -> Dict:
        """Update product inventory using SKU structure"""
        try:
            request = iop.IopRequest(INVENTORY_UPDATE_API, "POST")
            request.set_simplify()
            
            # Create sku_inventory JSON string as required by the API
            sku_inventory_data = [{"sku_id": sku_id, "inventory": inventory} for sku_id in sku_ids]
            sku_inventory_json = json.dumps(sku_inventory_data)
            
            # Add required parameters
            request.add_api_param('product_id', product_id)
            request.add_api_param('sku_inventory', sku_inventory_json)
            
            # Execute the request
            response = self.client.execute(request, self.access_token)
            
            result = {
                'product_id': product_id,
                'operation': 'sku_inventory',
                'value': inventory,
                'sku_ids': sku_ids,
                'success': response.code == "0",
                'code': response.code,
                'message': response.message,
                'request_id': response.request_id,
                'retry_count': retry_count
            }
            
            if response.code != "0":
                print(f"❌ Failed to update SKU inventory for product {product_id}: {response.message}")
                self.update_stats('failed')
                
                # Retry logic for certain error types (no delay for speed)
                if retry_count < MAX_RETRIES and response.code in ["500", "502", "503", "504"]:
                    print(f"   🔄 Retrying... (attempt {retry_count + 1}/{MAX_RETRIES})")
                    return self.update_sku_inventory(product_id, sku_ids, inventory, retry_count + 1)
            else:
                print(f"✅ Successfully updated SKU inventory for product {product_id} to {inventory} (SKUs: {', '.join(sku_ids)})")
                self.update_stats('successful')
                self.update_stats('sku_inventory_updates')
                
            return result
            
        except Exception as e:
            error_result = {
                'product_id': product_id,
                'operation': 'sku_inventory',
                'value': inventory,
                'sku_ids': sku_ids,
                'success': False,
                'code': 'ERROR',
                'message': str(e),
                'request_id': None,
                'retry_count': retry_count
            }
            print(f"❌ Exception updating SKU inventory for product {product_id}: {str(e)}")
            self.update_stats('failed')
            return error_result
    
    def update_direct_inventory(self, product_id: str, inventory: str, retry_count: int = 0) -> Dict:
        """Update product inventory using direct inventory structure"""
        try:
            request = iop.IopRequest(INVENTORY_UPDATE_API, "POST")
            request.set_simplify()
            
            # Add required parameters
            request.add_api_param('product_id', product_id)
            request.add_api_param('inventory', inventory)
            
            # Execute the request
            response = self.client.execute(request, self.access_token)
            
            result = {
                'product_id': product_id,
                'operation': 'direct_inventory',
                'value': inventory,
                'sku_ids': [],
                'success': response.code == "0",
                'code': response.code,
                'message': response.message,
                'request_id': response.request_id,
                'retry_count': retry_count
            }
            
            if response.code != "0":
                print(f"❌ Failed to update direct inventory for product {product_id}: {response.message}")
                self.update_stats('failed')
                
                # Retry logic for certain error types (no delay for speed)
                if retry_count < MAX_RETRIES and response.code in ["500", "502", "503", "504"]:
                    print(f"   🔄 Retrying... (attempt {retry_count + 1}/{MAX_RETRIES})")
                    return self.update_direct_inventory(product_id, inventory, retry_count + 1)
            else:
                print(f"✅ Successfully updated direct inventory for product {product_id} to {inventory}")
                self.update_stats('successful')
                self.update_stats('direct_inventory_updates')
                
            return result
            
        except Exception as e:
            error_result = {
                'product_id': product_id,
                'operation': 'direct_inventory',
                'value': inventory,
                'sku_ids': [],
                'success': False,
                'code': 'ERROR',
                'message': str(e),
                'request_id': None,
                'retry_count': retry_count
            }
            print(f"❌ Exception updating direct inventory for product {product_id}: {str(e)}")
            self.update_stats('failed')
            return error_result
    
    def process_single_row(self, row_data: tuple) -> Dict:
        """Process a single row of data (for concurrent processing)"""
        row_num, row = row_data
        try:
            spu_id = row['SPU_ID'].strip()
            price = row['price'].strip()
            inventory = row['inventory'].strip()
            
            print(f"\n🔄 Processing row {row_num}: SPU_ID {spu_id}")
            print(f"   Price: {price}, Inventory: {inventory}")
            
            # Perform vlookup to get product info
            product_info = self.get_product_info(spu_id)
            
            if not product_info:
                print(f"❌ SPU_ID {spu_id} not found in lookup table")
                self.update_stats('failed')
                self.update_progress()
                return {
                    'spu_id': spu_id,
                    'product_id': 'NOT_FOUND',
                    'operation': 'vlookup',
                    'value': inventory,
                    'sku_ids': [],
                    'success': False,
                    'code': 'SPU_NOT_FOUND',
                    'message': f"SPU_ID {spu_id} not found in lookup table",
                    'request_id': None,
                    'retry_count': 0
                }
            
            product_id = product_info['product_id']
            sku_ids = product_info['sku_ids']
            has_skus = product_info['has_skus']
            
            print(f"   Found Product_ID: {product_id}")
            print(f"   Has SKUs: {has_skus}")
            if has_skus:
                print(f"   SKU IDs: {', '.join(sku_ids)}")
            
            # Update inventory based on whether product has SKUs
            if has_skus:
                # Use SKU inventory structure
                inventory_result = self.update_sku_inventory(product_id, sku_ids, inventory)
            else:
                # Use direct inventory structure
                inventory_result = self.update_direct_inventory(product_id, inventory)
            
            # Add SPU_ID to result for tracking
            inventory_result['spu_id'] = spu_id
            self.update_stats('total_processed')
            self.update_progress()
            return inventory_result
            
        except ValueError as e:
            print(f"❌ Invalid data in row {row_num}: {e}")
            self.update_stats('failed')
            self.update_progress()
            return {
                'spu_id': row.get('SPU_ID', 'Unknown'),
                'product_id': 'UNKNOWN',
                'operation': 'validation',
                'value': '',
                'sku_ids': [],
                'success': False,
                'code': 'INVALID_DATA',
                'message': f"Invalid data: {e}",
                'request_id': None,
                'retry_count': 0
            }
        except Exception as e:
            print(f"❌ Error processing row {row_num}: {e}")
            self.update_stats('failed')
            self.update_progress()
            return {
                'spu_id': row.get('SPU_ID', 'Unknown'),
                'product_id': 'UNKNOWN',
                'operation': 'processing',
                'value': '',
                'sku_ids': [],
                'success': False,
                'code': 'PROCESSING_ERROR',
                'message': str(e),
                'request_id': None,
                'retry_count': 0
            }
    
    def process_csv_file(self, csv_file_path: str, max_workers: int = 10) -> List[Dict]:
        """Process CSV file and update inventories using vlookup with concurrent processing"""
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        print(f"📁 Reading CSV file: {csv_file_path}")
        print("=" * 60)
        
        # Read all rows first
        rows = []
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            # Validate CSV headers
            required_headers = ['SPU_ID', 'price', 'inventory']
            if not all(header in csv_reader.fieldnames for header in required_headers):
                raise ValueError(f"CSV must contain columns: {required_headers}")
            
            rows = list(enumerate(csv_reader, 1))
        
        # Set up progress tracking
        self.total_count = len(rows)
        self.start_time = time.time()
        self.processed_count = 0
        
        print(f"🚀 Processing {len(rows)} rows with {max_workers} concurrent workers")
        print("⚡ High-speed mode: No delays between requests")
        print("=" * 60)
        
        results = []
        
        # Process rows concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_row = {executor.submit(self.process_single_row, row_data): row_data for row_data in rows}
            
            # Collect results as they complete
            for future in as_completed(future_to_row):
                result = future.result()
                results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict], output_file: str = None):
        """Generate a comprehensive summary report"""
        if not output_file:
            output_file = f"inventory_update_report_{int(time.time())}.csv"
        
        successful_updates = [r for r in results if r.get('success', False)]
        failed_updates = [r for r in results if not r.get('success', False)]
        
        print("\n" + "=" * 60)
        print("📊 INVENTORY UPDATE SUMMARY REPORT")
        print("=" * 60)
        print(f"Total operations: {self.stats['total_processed']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"SKU inventory updates: {self.stats['sku_inventory_updates']}")
        print(f"Direct inventory updates: {self.stats['direct_inventory_updates']}")
        print(f"Success rate: {self.stats['successful']/self.stats['total_processed']*100:.1f}%" if self.stats['total_processed'] > 0 else "0%")
        
        if failed_updates:
            print("\n❌ FAILED UPDATES:")
            for failure in failed_updates[:10]:  # Show first 10 failures
                print(f"   SPU {failure.get('spu_id', 'Unknown')} -> Product {failure.get('product_id', 'Unknown')}: {failure.get('message', 'Unknown error')}")
            if len(failed_updates) > 10:
                print(f"   ... and {len(failed_updates) - 10} more failures")
        
        # Save detailed report to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['spu_id', 'product_id', 'operation', 'value', 'sku_ids', 'success', 'code', 'message', 'request_id', 'retry_count']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'spu_id': result.get('spu_id', ''),
                    'product_id': result.get('product_id', ''),
                    'operation': result.get('operation', ''),
                    'value': result.get('value', ''),
                    'sku_ids': ', '.join(result.get('sku_ids', [])),
                    'success': result.get('success', False),
                    'code': result.get('code', ''),
                    'message': result.get('message', ''),
                    'request_id': result.get('request_id', ''),
                    'retry_count': result.get('retry_count', 0)
                })
        
        print(f"\n📄 Detailed report saved to: {output_file}")
        
        # Save summary statistics to JSON
        stats_file = f"inventory_stats_{int(time.time())}.json"
        with open(stats_file, 'w', encoding='utf-8') as file:
            json.dump(self.stats, file, indent=2)
        print(f"📈 Statistics saved to: {stats_file}")

def main():
    """Main function"""
    try:
        print("🚀 Starting Alibaba.com High-Speed Inventory Updater with VLookup")
        print("=" * 70)
        print(f"App Key: {APP_KEY}")
        print(f"Access Token: {ACCESS_TOKEN[:20]}...")
        print(f"Base URL: {BASE_URL}")
        print(f"Request Delay: {REQUEST_DELAY}s (HIGH-SPEED MODE)")
        print(f"Max Retries: {MAX_RETRIES}")
        print(f"Concurrent Workers: 10")
        print(f"Sample CSV: {SAMPLE_CSV}")
        print(f"SKU Lookup CSV: {SKU_LOOKUP_CSV}")
        print("=" * 70)
        
        # Initialize updater
        updater = AlibabaInventoryUpdater(APP_KEY, APP_SECRET, ACCESS_TOKEN)
        
        # Load SKU lookup data
        start_time = time.time()
        updater.load_sku_lookup(SKU_LOOKUP_CSV)
        lookup_time = time.time() - start_time
        print(f"⏱️  SKU lookup loaded in {lookup_time:.2f} seconds")
        
        # Process sample CSV file
        process_start = time.time()
        results = updater.process_csv_file(SAMPLE_CSV, max_workers=10)
        process_time = time.time() - process_start
        
        # Generate report
        updater.generate_report(results)
        
        total_time = time.time() - start_time
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Total processing time: {total_time:.2f} seconds")
        print(f"   Processing rate: {len(results)/process_time:.2f} updates/second")
        print(f"   Lookup time: {lookup_time:.2f} seconds")
        print(f"   Pure processing time: {process_time:.2f} seconds")
        
        print("\n✅ High-speed process completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
