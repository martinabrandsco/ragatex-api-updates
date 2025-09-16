#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alibaba.com Product Price Updater with VLookup

This script reads product data from sample_product_updates.csv and performs
a vlookup against product_skus_ultra_fast.csv to determine the correct price structure.

CSV Format (sample_product_updates.csv):
SPU_ID,price,inventory
1601441057987,15.50,500
1601441012794,360,200

Usage:
    python3 alibaba_price_updater.py
"""

import iop
import csv
import sys
import os
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from typing import List, Dict, Optional
from collections import defaultdict
import queue
import multiprocessing as mp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
APP_KEY = os.getenv('APP_KEY', 'your_app_key_here')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', 'your_access_token_here')
APP_SECRET = os.getenv('APP_SECRET', 'your_app_secret_here')
BASE_URL = os.getenv('BASE_URL', 'https://openapi-api.alibaba.com/rest')
PRICE_UPDATE_API = "/icbu/product/edit-price"
REQUEST_DELAY = 0.01  # Minimal delay for maximum speed
MAX_RETRIES = 1  # Single retry for speed
BATCH_SIZE = 2000  # Larger batches for better performance
MAX_WORKERS = 50  # Maximum workers for speed
CHUNK_SIZE = 10000  # Larger chunks for efficiency
RATE_LIMIT_DELAY = 0.5  # Shorter delay when hitting rate limits
ADAPTIVE_DELAY = True  # Enable adaptive delay based on success rate

# File paths
SAMPLE_CSV = "sample_product_updates.csv"
SKU_LOOKUP_CSV = "product_skus_ultra_fast.csv"

class AlibabaPriceUpdater:
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
            'price_updates': 0,
            'sku_updates': 0,
            'direct_price_updates': 0
        }
        self.stats_lock = threading.Lock()  # Thread-safe statistics
        self.progress_lock = threading.Lock()  # Progress tracking
        self.processed_count = 0
        self.total_count = 0
        self.start_time = None
        self.rate_limit_count = 0
        self.success_count = 0
        self.current_delay = REQUEST_DELAY
        self.adaptive_delay_enabled = ADAPTIVE_DELAY
    
    def update_stats(self, key: str, increment: int = 1):
        """Thread-safe statistics update"""
        with self.stats_lock:
            self.stats[key] += increment
    
    def update_progress(self, increment: int = 1):
        """Update progress counter and display progress"""
        with self.progress_lock:
            self.processed_count += increment
            if self.total_count > 0 and self.start_time:
                elapsed = time.time() - self.start_time
                rate = self.processed_count / elapsed if elapsed > 0 else 0
                remaining = self.total_count - self.processed_count
                eta = remaining / rate if rate > 0 else 0
                
                progress_pct = (self.processed_count / self.total_count) * 100
                print(f"\r⚡ Progress: {self.processed_count:,}/{self.total_count:,} ({progress_pct:.1f}%) | "
                      f"Rate: {rate:.1f}/sec | ETA: {eta/60:.1f}min | Delay: {self.current_delay:.3f}s", end="", flush=True)
    
    def adjust_delay(self, was_rate_limited: bool = False, was_successful: bool = False):
        """Adaptive delay adjustment based on success rate and rate limiting"""
        if not self.adaptive_delay_enabled:
            return
            
        with self.stats_lock:
            if was_rate_limited:
                self.rate_limit_count += 1
                # Increase delay if rate limited
                self.current_delay = min(self.current_delay * 1.5, 0.1)
            elif was_successful:
                self.success_count += 1
                # Decrease delay if successful (but not below minimum)
                if self.success_count > 10 and self.rate_limit_count < 2:
                    self.current_delay = max(self.current_delay * 0.9, 0.001)
            
            # Reset counters periodically
            if (self.success_count + self.rate_limit_count) > 100:
                self.success_count = 0
                self.rate_limit_count = 0
    
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
    
    def update_sku_price(self, product_id: str, sku_ids: List[str], price: str, retry_count: int = 0) -> Dict:
        """Update product price using SKU structure"""
        try:
            request = iop.IopRequest(PRICE_UPDATE_API, "POST")
            request.set_simplify()
            
            # Create sku_price JSON string as required by the API
            sku_price_data = [{"price": price, "sku_id": sku_id} for sku_id in sku_ids]
            sku_price_json = json.dumps(sku_price_data)
            
            # Add required parameters
            request.add_api_param('product_id', product_id)
            request.add_api_param('sku_price', sku_price_json)
            
            # Execute the request
            response = self.client.execute(request, self.access_token)
            
            result = {
                'product_id': product_id,
                'operation': 'sku_price',
                'value': price,
                'sku_ids': sku_ids,
                'success': response.code == "0",
                'code': response.code,
                'message': response.message,
                'request_id': response.request_id,
                'retry_count': retry_count
            }
            
            if response.code != "0":
                # Handle rate limiting
                if "frequency exceeds the limit" in response.message or response.code == "429":
                    self.adjust_delay(was_rate_limited=True)
                    time.sleep(RATE_LIMIT_DELAY)
                    self.update_stats('failed')
                    return self.update_sku_price(product_id, sku_ids, price, retry_count + 1)
                else:
                    print(f"❌ Failed to update SKU price for product {product_id}: {response.message}")
                    self.update_stats('failed')
                
                # Retry logic for certain error types
                if retry_count < MAX_RETRIES and response.code in ["500", "502", "503", "504"]:
                    return self.update_sku_price(product_id, sku_ids, price, retry_count + 1)
            else:
                print(f"✅ Successfully updated SKU price for product {product_id} to {price} (SKUs: {', '.join(sku_ids)})")
                self.update_stats('successful')
                self.update_stats('sku_updates')
                self.adjust_delay(was_successful=True)
                
            return result
            
        except Exception as e:
            error_result = {
                'product_id': product_id,
                'operation': 'sku_price',
                'value': price,
                'sku_ids': sku_ids,
                'success': False,
                'code': 'ERROR',
                'message': str(e),
                'request_id': None,
                'retry_count': retry_count
            }
            print(f"❌ Exception updating SKU price for product {product_id}: {str(e)}")
            self.update_stats('failed')
            return error_result
    
    def update_direct_price(self, product_id: str, price: str, retry_count: int = 0) -> Dict:
        """Update product price using direct price structure"""
        try:
            request = iop.IopRequest(PRICE_UPDATE_API, "POST")
            request.set_simplify()
            
            # Create price JSON string as required by the API
            price_data = {
                "price_type": "TIERED",
                "tiered_price": [
                    {"quantity": "1", "price": price}
                ]
            }
            price_json = json.dumps(price_data)
            
            # Add required parameters
            request.add_api_param('product_id', product_id)
            request.add_api_param('price', price_json)
            
            # Execute the request
            response = self.client.execute(request, self.access_token)
            
            result = {
                'product_id': product_id,
                'operation': 'direct_price',
                'value': price,
                'sku_ids': [],
                'success': response.code == "0",
                'code': response.code,
                'message': response.message,
                'request_id': response.request_id,
                'retry_count': retry_count
            }
            
            if response.code != "0":
                # Handle rate limiting
                if "frequency exceeds the limit" in response.message or response.code == "429":
                    self.adjust_delay(was_rate_limited=True)
                    time.sleep(RATE_LIMIT_DELAY)
                    self.update_stats('failed')
                    return self.update_direct_price(product_id, price, retry_count + 1)
                else:
                    print(f"❌ Failed to update direct price for product {product_id}: {response.message}")
                    self.update_stats('failed')
                
                # Retry logic for certain error types
                if retry_count < MAX_RETRIES and response.code in ["500", "502", "503", "504"]:
                    return self.update_direct_price(product_id, price, retry_count + 1)
            else:
                print(f"✅ Successfully updated direct price for product {product_id} to {price}")
                self.update_stats('successful')
                self.update_stats('direct_price_updates')
                self.adjust_delay(was_successful=True)
                
            return result
            
        except Exception as e:
            error_result = {
                'product_id': product_id,
                'operation': 'direct_price',
                'value': price,
                'sku_ids': [],
                'success': False,
                'code': 'ERROR',
                'message': str(e),
                'request_id': None,
                'retry_count': retry_count
            }
            print(f"❌ Exception updating direct price for product {product_id}: {str(e)}")
            self.update_stats('failed')
            return error_result
        
    def update_price(self, product_id: str, price: float, sku_id: str, retry_count: int = 0) -> Dict:
        """Update product price with retry logic"""
        try:
            request = iop.IopRequest(PRICE_UPDATE_API, "POST")
            request.set_simplify()
            
            # Create sku_price JSON string as required by the API
            sku_price_data = [{
                "price": str(price),
                "sku_id": str(sku_id)
            }]
            sku_price_json = json.dumps(sku_price_data)
            
            # Add required parameters
            request.add_api_param('product_id', product_id)
            request.add_api_param('sku_price', sku_price_json)
            
            # Execute the request
            response = self.client.execute(request, self.access_token)
            
            result = {
                'product_id': product_id,
                'operation': 'price',
                'value': price,
                'sku_id': sku_id,
                'success': response.code == "0",
                'code': response.code,
                'message': response.message,
                'request_id': response.request_id,
                'retry_count': retry_count
            }
            
            if response.code != "0":
                print(f"❌ Failed to update price for product {product_id}: {response.message}")
                self.stats['failed'] += 1
                
                # Retry logic for certain error types
                if retry_count < MAX_RETRIES and response.code in ["500", "502", "503", "504"]:
                    print(f"   🔄 Retrying... (attempt {retry_count + 1}/{MAX_RETRIES})")
                    time.sleep(REQUEST_DELAY * 2)  # Longer delay for retries
                    return self.update_price(product_id, price, sku_id, retry_count + 1)
            else:
                print(f"✅ Successfully updated price for product {product_id} to {price} (SKU: {sku_id})")
                self.stats['successful'] += 1
                self.stats['price_updates'] += 1
                
            return result
            
        except Exception as e:
            error_result = {
                'product_id': product_id,
                'operation': 'price',
                'value': price,
                'sku_id': sku_id,
                'success': False,
                'code': 'ERROR',
                'message': str(e),
                'request_id': None,
                'retry_count': retry_count
            }
            print(f"❌ Exception updating price for product {product_id}: {str(e)}")
            self.stats['failed'] += 1
            return error_result
    
    def process_single_row(self, row_data: tuple) -> Dict:
        """Process a single row of data (for concurrent processing) - Optimized for speed"""
        row_num, row = row_data
        try:
            spu_id = row['SPU_ID'].strip()
            price = row['price'].strip()
            
            # Perform vlookup to get product info
            product_info = self.get_product_info(spu_id)
            
            if not product_info:
                self.update_stats('failed')
                self.update_progress()
                return {
                    'spu_id': spu_id,
                    'product_id': 'NOT_FOUND',
                    'operation': 'vlookup',
                    'value': price,
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
            
            # Update price based on whether product has SKUs
            if has_skus:
                # Use SKU price structure
                price_result = self.update_sku_price(product_id, sku_ids, price)
            else:
                # Use direct price structure
                price_result = self.update_direct_price(product_id, price)
            
            # Add SPU_ID to result for tracking
            price_result['spu_id'] = spu_id
            self.update_progress()
            
            # Adaptive delay to prevent rate limiting
            time.sleep(self.current_delay)
            return price_result
            
        except Exception as e:
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
    
    def process_chunk(self, chunk_rows: List[tuple]) -> List[Dict]:
        """Process a chunk of rows with maximum concurrency"""
        results = []
        
        # Use maximum workers for each chunk
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks in the chunk
            future_to_row = {executor.submit(self.process_single_row, row_data): row_data for row_data in chunk_rows}
            
            # Collect results as they complete
            for future in as_completed(future_to_row):
                result = future.result()
                results.append(result)
        
        return results
    
    def process_csv_file(self, csv_file_path: str, max_workers: int = MAX_WORKERS) -> List[Dict]:
        """Process CSV file with maximum performance - optimized for 200k+ products"""
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        print(f"📁 Reading CSV file: {csv_file_path}")
        print("=" * 80)
        
        # Count total rows first for progress tracking
        print("🔍 Counting total rows...")
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            required_headers = ['SPU_ID', 'price', 'inventory']
            if not all(header in csv_reader.fieldnames for header in required_headers):
                raise ValueError(f"CSV must contain columns: {required_headers}")
            
            # Count rows efficiently
            total_rows = sum(1 for _ in csv_reader)
        
        self.total_count = total_rows
        self.start_time = time.time()
        
        print(f"🚀 Processing {total_rows:,} rows with {MAX_WORKERS} concurrent workers")
        print(f"⚡ ADAPTIVE ULTRA-HIGH-SPEED mode: Dynamic delays, chunked processing")
        print(f"📦 Chunk size: {CHUNK_SIZE:,} rows per chunk")
        print(f"🎯 Target: Maximum speed while respecting API limits")
        print("=" * 80)
        
        all_results = []
        chunk_count = 0
        
        # Process file in chunks to manage memory
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            chunk_rows = []
            
            for row_num, row in enumerate(csv_reader, 1):
                chunk_rows.append((row_num, row))
                
                # Process chunk when it reaches CHUNK_SIZE
                if len(chunk_rows) >= CHUNK_SIZE:
                    chunk_count += 1
                    print(f"\n📦 Processing chunk {chunk_count} ({len(chunk_rows):,} rows)...")
                    
                    chunk_results = self.process_chunk(chunk_rows)
                    all_results.extend(chunk_results)
                    
                    # Clear chunk to free memory
                    chunk_rows = []
                    
                    # Show progress
                    processed_so_far = len(all_results)
                    print(f"✅ Chunk {chunk_count} completed. Total processed: {processed_so_far:,}/{total_rows:,}")
            
            # Process remaining rows in final chunk
            if chunk_rows:
                chunk_count += 1
                print(f"\n📦 Processing final chunk {chunk_count} ({len(chunk_rows):,} rows)...")
                
                chunk_results = self.process_chunk(chunk_rows)
                all_results.extend(chunk_results)
        
        print(f"\n✅ All chunks processed! Total results: {len(all_results):,}")
        return all_results
    
    def generate_report(self, results: List[Dict], output_file: str = None):
        """Generate a comprehensive summary report"""
        if not output_file:
            output_file = f"price_update_report_{int(time.time())}.csv"
        
        successful_updates = [r for r in results if r.get('success', False)]
        failed_updates = [r for r in results if not r.get('success', False)]
        
        print("\n" + "=" * 60)
        print("📊 PRICE UPDATE SUMMARY REPORT")
        print("=" * 60)
        print(f"Total operations: {self.stats['total_processed']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"SKU price updates: {self.stats['sku_updates']}")
        print(f"Direct price updates: {self.stats['direct_price_updates']}")
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
        stats_file = f"price_stats_{int(time.time())}.json"
        with open(stats_file, 'w', encoding='utf-8') as file:
            json.dump(self.stats, file, indent=2)
        print(f"📈 Statistics saved to: {stats_file}")

def main():
    """Main function - Ultra High-Speed Mode for 200k+ products"""
    try:
        print("🚀 Starting Alibaba.com ULTRA HIGH-SPEED Price Updater")
        print("=" * 80)
        print(f"App Key: {APP_KEY}")
        print(f"Access Token: {ACCESS_TOKEN[:20]}...")
        print(f"Base URL: {BASE_URL}")
        print(f"Request Delay: {REQUEST_DELAY}s (ADAPTIVE ULTRA HIGH-SPEED MODE)")
        print(f"Max Retries: {MAX_RETRIES}")
        print(f"Concurrent Workers: {MAX_WORKERS}")
        print(f"Chunk Size: {CHUNK_SIZE:,} rows")
        print(f"Rate Limit Delay: {RATE_LIMIT_DELAY}s")
        print(f"Adaptive Delay: {ADAPTIVE_DELAY}")
        print(f"Sample CSV: {SAMPLE_CSV}")
        print(f"SKU Lookup CSV: {SKU_LOOKUP_CSV}")
        print("=" * 80)
        
        # Initialize updater
        updater = AlibabaPriceUpdater(APP_KEY, APP_SECRET, ACCESS_TOKEN)
        
        # Load SKU lookup data
        start_time = time.time()
        updater.load_sku_lookup(SKU_LOOKUP_CSV)
        lookup_time = time.time() - start_time
        print(f"⏱️  SKU lookup loaded in {lookup_time:.2f} seconds")
        
        # Process sample CSV file
        process_start = time.time()
        results = updater.process_csv_file(SAMPLE_CSV, max_workers=MAX_WORKERS)
        process_time = time.time() - process_start
        
        # Generate report
        updater.generate_report(results)
        
        total_time = time.time() - start_time
        print(f"\n⚡ ULTRA HIGH-SPEED PERFORMANCE METRICS:")
        print(f"   Total processing time: {total_time:.2f} seconds")
        print(f"   Processing rate: {len(results)/process_time:.2f} updates/second")
        print(f"   Lookup time: {lookup_time:.2f} seconds")
        print(f"   Pure processing time: {process_time:.2f} seconds")
        print(f"   Memory efficiency: Chunked processing")
        print(f"   Concurrency: {MAX_WORKERS} workers per chunk")
        
        # Estimate for 200k products
        if len(results) > 0:
            estimated_200k_time = (200000 / len(results)) * process_time
            print(f"\n📊 ESTIMATED PERFORMANCE FOR 200K PRODUCTS:")
            print(f"   Estimated time: {estimated_200k_time/60:.1f} minutes")
            print(f"   Estimated rate: {200000/estimated_200k_time:.0f} updates/second")
            print(f"   Final delay: {updater.current_delay:.3f}s")
            print(f"   Rate limits hit: {updater.rate_limit_count}")
            print(f"   Success rate: {(updater.success_count/(updater.success_count + updater.rate_limit_count)*100):.1f}%")
        
        print("\n✅ Ultra high-speed process completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
