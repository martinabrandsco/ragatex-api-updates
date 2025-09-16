#!/usr/bin/env python3
"""
Alibaba Product Updater Web Application

A Flask web application that allows users to upload CSV files and update
product prices or inventory on Alibaba.com using the optimized updater scripts.

Usage:
    python3 app.py
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import json
import threading
import time
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our updater classes
from alibaba_price_updater import AlibabaPriceUpdater
from alibaba_inventory_updater import AlibabaInventoryUpdater

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Global variables for tracking progress
progress_data = {}
active_jobs = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Validate CSV structure
        try:
            import csv
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                # Check required columns
                required_headers = ['SPU_ID', 'price', 'inventory']
                if not all(header in headers for header in required_headers):
                    os.remove(filepath)
                    return jsonify({'error': f'CSV must contain columns: {required_headers}'}), 400
                
                # Count rows
                row_count = sum(1 for _ in reader)
                
                return jsonify({
                    'success': True,
                    'filename': unique_filename,
                    'row_count': row_count,
                    'headers': headers
                })
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': f'Invalid CSV file: {str(e)}'}), 400
    
    return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400

@app.route('/start_update', methods=['POST'])
def start_update():
    """Start the update process"""
    data = request.get_json()
    filename = data.get('filename')
    update_type = data.get('update_type')  # 'price' or 'inventory'
    
    if not filename or not update_type:
        return jsonify({'error': 'Missing filename or update type'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 400
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Initialize progress tracking
    progress_data[job_id] = {
        'status': 'starting',
        'progress': 0,
        'total': 0,
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'current_rate': 0,
        'eta_minutes': 0,
        'start_time': time.time(),
        'update_type': update_type,
        'filename': filename
    }
    
    # Start update process in background thread
    thread = threading.Thread(target=run_update, args=(job_id, filepath, update_type))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'job_id': job_id})

def run_update(job_id, filepath, update_type):
    """Run the update process in background"""
    try:
        progress_data[job_id]['status'] = 'running'
        
        # Reload environment variables in the background thread
        load_dotenv()
        
        # Get credentials from environment
        app_key = os.getenv('APP_KEY', 'your_app_key_here')
        app_secret = os.getenv('APP_SECRET', 'your_app_secret_here')
        access_token = os.getenv('ACCESS_TOKEN', 'your_access_token_here')
        
        # Debug: Print credentials (first few characters only for security)
        print(f"🔑 Loaded credentials - APP_KEY: {app_key[:8]}..., APP_SECRET: {app_secret[:8]}..., ACCESS_TOKEN: {access_token[:8]}...")
        
        # Validate credentials
        if app_key == 'your_app_key_here' or app_secret == 'your_app_secret_here' or access_token == 'your_access_token_here':
            progress_data[job_id]['status'] = 'error'
            progress_data[job_id]['error'] = 'API credentials not configured. Please set up your .env file with valid credentials.'
            return
        
        # Initialize updater based on type
        if update_type == 'price':
            updater = AlibabaPriceUpdater(
                app_key=app_key,
                app_secret=app_secret,
                access_token=access_token
            )
        else:  # inventory
            updater = AlibabaInventoryUpdater(
                app_key=app_key,
                app_secret=app_secret,
                access_token=access_token
            )
        
        # Load SKU lookup data
        progress_data[job_id]['status'] = 'loading_lookup'
        updater.load_sku_lookup('product_skus_ultra_fast.csv')
        
        # Set up progress tracking
        original_update_progress = updater.update_progress
        original_update_stats = updater.update_stats
        
        def track_progress(increment=1):
            original_update_progress(increment)
            progress_data[job_id]['processed'] = updater.processed_count
            progress_data[job_id]['total'] = updater.total_count
            progress_data[job_id]['progress'] = (updater.processed_count / updater.total_count * 100) if updater.total_count > 0 else 0
            progress_data[job_id]['successful'] = updater.stats['successful']
            progress_data[job_id]['failed'] = updater.stats['failed']
            
            # Calculate rate and ETA
            elapsed = time.time() - progress_data[job_id]['start_time']
            if elapsed > 0:
                progress_data[job_id]['current_rate'] = updater.processed_count / elapsed
                remaining = updater.total_count - updater.processed_count
                if progress_data[job_id]['current_rate'] > 0:
                    progress_data[job_id]['eta_minutes'] = remaining / progress_data[job_id]['current_rate'] / 60
        
        def track_stats(key, increment=1):
            original_update_stats(key, increment)
            progress_data[job_id]['successful'] = updater.stats['successful']
            progress_data[job_id]['failed'] = updater.stats['failed']
        
        # Replace methods with tracking versions
        updater.update_progress = track_progress
        updater.update_stats = track_stats
        
        # Process the file
        progress_data[job_id]['status'] = 'processing'
        results = updater.process_csv_file(filepath)
        
        # Generate report
        report_filename = f"update_report_{job_id}_{int(time.time())}.csv"
        updater.generate_report(results, report_filename)
        
        # Update final status
        progress_data[job_id]['status'] = 'completed'
        progress_data[job_id]['report_file'] = report_filename
        progress_data[job_id]['final_stats'] = {
            'total_processed': updater.stats['total_processed'],
            'successful': updater.stats['successful'],
            'failed': updater.stats['failed'],
            'success_rate': (updater.stats['successful'] / updater.stats['total_processed'] * 100) if updater.stats['total_processed'] > 0 else 0
        }
        
    except Exception as e:
        progress_data[job_id]['status'] = 'error'
        progress_data[job_id]['error'] = str(e)

@app.route('/progress/<job_id>')
def get_progress(job_id):
    """Get progress for a specific job"""
    if job_id not in progress_data:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(progress_data[job_id])

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated report file"""
    filepath = os.path.join('.', filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/cleanup/<job_id>')
def cleanup_job(job_id):
    """Clean up job data and files"""
    if job_id in progress_data:
        # Clean up uploaded file
        if 'filename' in progress_data[job_id]:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], progress_data[job_id]['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
        
        # Clean up report file
        if 'report_file' in progress_data[job_id]:
            report_path = progress_data[job_id]['report_file']
            if os.path.exists(report_path):
                os.remove(report_path)
        
        # Remove job data
        del progress_data[job_id]
    
    return jsonify({'success': True})

if __name__ == '__main__':
    print("🚀 Starting Alibaba Product Updater Web Application")
    print("=" * 60)
    print("📱 Web Interface: http://localhost:8080")
    print("📁 Upload Directory: uploads/")
    print("📊 Progress Tracking: Real-time updates")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)
