#!/usr/bin/env python3
"""
Test script for inventory updates in the Alibaba Product Updater Web Application
"""

import requests
import time
import os

def test_inventory_update():
    """Test inventory update functionality"""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Inventory Update in Web Application")
    print("=" * 60)
    
    # Test 1: Check if the web app is running
    print("1. Testing web application availability...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Web application is running")
        else:
            print(f"   ❌ Web application returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Web application is not running: {e}")
        return False
    
    # Test 2: Create a test CSV file
    print("\n2. Creating test CSV file...")
    test_csv_content = """SPU_ID,price,inventory
8718696170731,96,500
5025155028100,600,200
8718696176313,150,300"""
    
    test_csv_path = "test_inventory_upload.csv"
    with open(test_csv_path, 'w') as f:
        f.write(test_csv_content)
    print("   ✅ Test CSV file created")
    
    # Test 3: Test file upload
    print("\n3. Testing file upload...")
    try:
        with open(test_csv_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/upload", files=files, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ File upload successful")
                filename = data['filename']
                print(f"   📁 Uploaded file: {filename}")
            else:
                print(f"   ❌ File upload failed: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Upload request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ File upload error: {e}")
        return False
    
    # Test 4: Test inventory update start
    print("\n4. Testing inventory update start...")
    try:
        update_data = {
            'filename': filename,
            'update_type': 'inventory'
        }
        response = requests.post(f"{base_url}/start_update", 
                               json=update_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Inventory update started successfully")
                job_id = data['job_id']
                print(f"   🆔 Job ID: {job_id}")
            else:
                print(f"   ❌ Inventory update start failed: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Update start request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Update start error: {e}")
        return False
    
    # Test 5: Test progress tracking
    print("\n5. Testing progress tracking...")
    try:
        for i in range(10):  # Check progress 10 times
            time.sleep(2)
            response = requests.get(f"{base_url}/progress/{job_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   📊 Progress: {data.get('progress', 0):.1f}% - Status: {data.get('status', 'unknown')}")
                if data.get('status') in ['completed', 'error']:
                    if data.get('status') == 'completed':
                        print("   ✅ Inventory update completed successfully!")
                        if 'final_stats' in data:
                            stats = data['final_stats']
                            print(f"   📈 Final Stats: {stats['successful']}/{stats['total_processed']} successful ({stats['success_rate']:.1f}%)")
                    else:
                        print(f"   ❌ Inventory update failed: {data.get('error', 'Unknown error')}")
                    break
            else:
                print(f"   ❌ Progress request failed with status {response.status_code}")
                break
    except Exception as e:
        print(f"   ❌ Progress tracking error: {e}")
    
    # Cleanup
    print("\n6. Cleaning up...")
    try:
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
        print("   ✅ Test files cleaned up")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")
    
    print("\n🎉 Inventory update test completed!")
    return True

if __name__ == "__main__":
    test_inventory_update()
