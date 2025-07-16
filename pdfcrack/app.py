#!/usr/bin/env python3
"""
PDF Unlock Web Application
Modern Flask-based web interface for PDF password cracking and unlocking
"""

import os
import tempfile
import uuid
from flask import Flask, request, jsonify, render_template, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import threading
import time
from typing import Dict, Any
import json

# Import our existing PDF processing modules
from pdf_unlock_simple import unlock_pdf
from pdf_crack_simple import analyze_pdf
try:
    from watermark_remover import remove_watermarks
except ImportError:
    from watermark_remover_fallback import remove_watermarks

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Store for tracking job progress
job_status: Dict[str, Dict[str, Any]] = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_jobs():
    """Clean up old job data and files"""
    current_time = time.time()
    expired_jobs = []
    
    for job_id, job_data in job_status.items():
        if current_time - job_data.get('created_at', 0) > 3600:  # 1 hour
            expired_jobs.append(job_id)
            # Clean up temporary files
            if 'input_file' in job_data and os.path.exists(job_data['input_file']):
                os.remove(job_data['input_file'])
            if 'output_file' in job_data and os.path.exists(job_data['output_file']):
                os.remove(job_data['output_file'])
    
    for job_id in expired_jobs:
        del job_status[job_id]

def process_pdf_async(job_id: str, input_path: str, output_path: str, password: str = None, use_crack: bool = False, remove_watermark: bool = True):
    """Process PDF in background thread with watermark removal"""
    try:
        job_status[job_id]['status'] = 'processing'
        job_status[job_id]['progress'] = 10
        
        # Step 1: Unlock the PDF
        if use_crack:
            job_status[job_id]['message'] = 'Analyzing PDF encryption...'
            job_status[job_id]['progress'] = 20
            
            # Try to crack the password
            cracked_password = analyze_pdf(input_path)
            
            if cracked_password is not None:
                job_status[job_id]['message'] = 'Bypass successful, unlocking PDF...'
                job_status[job_id]['progress'] = 40
                success, error = unlock_pdf(input_path, output_path, cracked_password)
            else:
                job_status[job_id]['status'] = 'failed'
                job_status[job_id]['error'] = 'Unable to bypass PDF protection'
                return
        else:
            job_status[job_id]['message'] = 'Unlocking PDF with provided password...'
            job_status[job_id]['progress'] = 30
            success, error = unlock_pdf(input_path, output_path, password or '')
        
        if not success:
            job_status[job_id]['status'] = 'failed'
            job_status[job_id]['error'] = error
            return
        
        # Step 2: Remove watermarks if requested
        if remove_watermark:
            job_status[job_id]['message'] = 'Removing watermarks...'
            job_status[job_id]['progress'] = 60
            
            # Create temporary file for watermark removal
            temp_dir = tempfile.gettempdir()
            watermark_output = os.path.join(temp_dir, f"{job_id}_no_watermark.pdf")
            
            try:
                wm_success, wm_error, wm_stats = remove_watermarks(output_path, watermark_output)
                
                if wm_success:
                    # Replace the original output with watermark-free version
                    os.replace(watermark_output, output_path)
                    job_status[job_id]['progress'] = 80
                    job_status[job_id]['watermark_stats'] = wm_stats
                    
                    # Log watermark removal stats
                    total_removed = (wm_stats.get('text_watermarks_removed', 0) + 
                                   wm_stats.get('image_watermarks_removed', 0) + 
                                   wm_stats.get('transparent_objects_removed', 0) + 
                                   wm_stats.get('background_objects_removed', 0))
                    
                    if total_removed > 0:
                        job_status[job_id]['message'] = f'Removed {total_removed} watermark elements!'
                    else:
                        job_status[job_id]['message'] = 'PDF processed safely - no watermarks detected'
                    
                    # Check if there was a safety warning
                    if wm_error and 'original file' in wm_error:
                        job_status[job_id]['message'] = 'PDF processed safely (watermark removal skipped for file integrity)'
                        job_status[job_id]['safety_note'] = wm_error
                else:
                    # Watermark removal failed, but PDF is still unlocked
                    job_status[job_id]['message'] = f'PDF unlocked (watermark removal skipped: {wm_error})'
                    job_status[job_id]['watermark_error'] = wm_error
                    
            except Exception as wm_exception:
                # Continue with unlocked PDF even if watermark removal fails
                job_status[job_id]['message'] = f'PDF unlocked, watermark removal error: {str(wm_exception)}'
                job_status[job_id]['watermark_error'] = str(wm_exception)
        
        # Final completion
        job_status[job_id]['status'] = 'completed'
        job_status[job_id]['progress'] = 100
        job_status[job_id]['message'] = 'PDF processing completed successfully!'
        job_status[job_id]['output_file'] = output_path
        
    except Exception as e:
        job_status[job_id]['status'] = 'failed'
        job_status[job_id]['error'] = f'Unexpected error: {str(e)}'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    cleanup_old_jobs()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        input_path = os.path.join(temp_dir, f"{job_id}_input_{filename}")
        output_path = os.path.join(temp_dir, f"{job_id}_output_{filename}")
        
        file.save(input_path)
        
        # Get form data
        password = request.form.get('password', '').strip()
        use_crack = request.form.get('use_crack') == 'true'
        remove_watermark = request.form.get('remove_watermark', 'true') == 'true'
        
        # Initialize job status
        job_status[job_id] = {
            'status': 'queued',
            'progress': 0,
            'message': 'Job queued...',
            'created_at': time.time(),
            'input_file': input_path,
            'filename': filename
        }
        
        # Start background processing
        thread = threading.Thread(
            target=process_pdf_async,
            args=(job_id, input_path, output_path, password, use_crack, remove_watermark)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'job_id': job_id})
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/status/<job_id>')
def get_status(job_id):
    if job_id not in job_status:
        return jsonify({'error': 'Job not found'}), 404
    
    job_data = job_status[job_id].copy()
    # Remove file paths from response for security
    job_data.pop('input_file', None)
    job_data.pop('output_file', None)
    
    return jsonify(job_data)

@app.route('/download/<job_id>')
def download_file(job_id):
    if job_id not in job_status:
        return jsonify({'error': 'Job not found'}), 404
    
    job_data = job_status[job_id]
    if job_data['status'] != 'completed':
        return jsonify({'error': 'Job not completed'}), 400
    
    if 'output_file' not in job_data or not os.path.exists(job_data['output_file']):
        return jsonify({'error': 'Output file not found'}), 404
    
    filename = f"unlocked_{job_data['filename']}"
    return send_file(
        job_data['output_file'],
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting PDF Unlock Pro Web Application...")
    print("📡 Server will be available at: http://localhost:5000")
    print("🎨 Features: PDF Unlock + Watermark Removal + Modern UI")
    print("🛡️ Safe Mode: File integrity protection enabled")
    app.run(debug=True, host='0.0.0.0', port=5000)