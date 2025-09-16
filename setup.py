#!/usr/bin/env python3
"""
Setup script for Alibaba Product Updater
"""

import os
import shutil
import subprocess
import sys

def main():
    print("🚀 Setting up Alibaba Product Updater")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        if os.path.exists('config.env'):
            print("📋 Creating .env file from config.env...")
            shutil.copy('config.env', '.env')
            print("✅ .env file created!")
            print("⚠️  Please edit .env file with your actual Alibaba API credentials")
        else:
            print("❌ config.env file not found!")
            return False
    else:
        print("✅ .env file already exists")
    
    # Install dependencies
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Create uploads directory
    print("\n📁 Creating uploads directory...")
    os.makedirs('uploads', exist_ok=True)
    print("✅ Uploads directory created!")
    
    # Check for required files
    print("\n🔍 Checking required files...")
    required_files = [
        'product_skus_ultra_fast.csv',
        'alibaba_price_updater.py',
        'alibaba_inventory_updater.py',
        'app.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files present!")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your Alibaba API credentials")
    print("2. Run: python3 app.py")
    print("3. Open: http://localhost:8080")
    
    return True

if __name__ == "__main__":
    main()
