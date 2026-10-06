#!/usr/bin/env python3
"""
Web GUI for Multi-Language Scraper
Docker-compatible web interface
"""

from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import subprocess
import json
import os
import sys
import threading
import time
from pathlib import Path
from datetime import datetime
import uuid

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
CORS(app)

# Global state
scrapes = {}
active_tasks = {}


class ScraperTask:
    """Background scraper task"""
    
    def __init__(self, task_id, url, language, options):
        self.task_id = task_id
        self.url = url
        self.language = language
        self.options = options
        self.status = 'pending'
        self.progress = 0
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
        self.log = []
    
    def run(self):
        """Run the scraper task"""
        self.status = 'running'
        self.started_at = datetime.now()
        self.log.append(f"Started at {self.started_at}")
        
        try:
            # Build command based on language
            if self.language == 'python':
                cmd = ['python', 'cli.py', '--url', self.url]
            elif self.language == 'rust':
                rust_path = Path('rust-scraper/target/release/turbo-scraper')
                cmd = [str(rust_path), self.url]
            elif self.language == 'go':
                go_path = Path('go-scraper/turbo-scraper')
                cmd = [str(go_path), self.url]
            elif self.language == 'collaborative':
                cmd = ['python', 'team_scrape.py', self.url]
            else:
                raise ValueError(f"Unknown language: {self.language}")
            
            # Add options
            if self.options.get('ctf_mode'):
                cmd.append('--ctf-mode')
            if self.options.get('max_depth'):
                cmd.extend(['--max-depth', str(self.options['max_depth'])])
            if self.options.get('max_pages'):
                cmd.extend(['--max-pages', str(self.options['max_pages'])])
            if self.options.get('files_only'):
                cmd.append('--files-only')
            if self.options.get('fetch_resources'):
                cmd.append('--fetch-resources')
            
            self.log.append(f"Running: {' '.join(cmd)}")
            
            # Run the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )
            
            # Monitor progress
            while True:
                if process.poll() is not None:
                    break
                time.sleep(0.5)
                self.progress = min(self.progress + 5, 90)
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.status = 'completed'
                self.progress = 100
                self.completed_at = datetime.now()
                self.result = {
                    'stdout': stdout,
                    'files_downloaded': self.count_files()
                }
                self.log.append(f"Completed at {self.completed_at}")
                self.log.append(f"Exit code: {process.returncode}")
            else:
                self.status = 'failed'
                self.error = stderr
                self.log.append(f"Failed: {stderr}")
        
        except Exception as e:
            self.status = 'failed'
            self.error = str(e)
            self.log.append(f"Error: {str(e)}")
    
    def count_files(self):
        """Count downloaded files"""
        data_dir = Path('data')
        if data_dir.exists():
            return sum(1 for _ in data_dir.rglob('*') if _.is_file())
        return 0


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """Start a new scrape task"""
    data = request.json
    
    url = data.get('url')
    language = data.get('language', 'python')
    options = data.get('options', {})
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Create task
    task_id = str(uuid.uuid4())
    task = ScraperTask(task_id, url, language, options)
    active_tasks[task_id] = task
    
    # Run in background thread
    thread = threading.Thread(target=task.run)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'status': 'started',
        'url': url,
        'language': language
    })


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get task status"""
    if task_id not in active_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = active_tasks[task_id]
    
    return jsonify({
        'task_id': task.task_id,
        'url': task.url,
        'language': task.language,
        'status': task.status,
        'progress': task.progress,
        'log': task.log,
        'error': task.error,
        'result': task.result,
        'started_at': task.started_at.isoformat() if task.started_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None
    })


@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """List all tasks"""
    return jsonify({
        'tasks': [
            {
                'task_id': task.task_id,
                'url': task.url,
                'language': task.language,
                'status': task.status,
                'progress': task.progress,
                'started_at': task.started_at.isoformat() if task.started_at else None
            }
            for task in active_tasks.values()
        ]
    })


@app.route('/api/files', methods=['GET'])
def list_files():
    """List downloaded files"""
    data_dir = Path('data')
    
    if not data_dir.exists():
        return jsonify({'files': []})
    
    files = []
    for file_path in data_dir.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(data_dir)
            files.append({
                'name': str(relative_path),
                'size': file_path.stat().st_size,
                'path': str(file_path)
            })
    
    return jsonify({'files': files})


@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download a file"""
    file_path = Path('data') / filename
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True)


@app.route('/api/download-all', methods=['GET'])
def download_all():
    """Download all files as zip"""
    import zipfile
    import io
    
    data_dir = Path('data')
    
    if not data_dir.exists():
        return jsonify({'error': 'No files to download'}), 404
    
    # Create zip in memory
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in data_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(data_dir)
                zf.write(file_path, arcname)
    
    memory_file.seek(0)
    
    @after_this_request
    def remove_file(response):
        return response
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='scraped_files.zip'
    )


@app.route('/api/clear-files', methods=['POST'])
def clear_files():
    """Clear all downloaded files"""
    import shutil
    
    data_dir = Path('data')
    
    if data_dir.exists():
        shutil.rmtree(data_dir)
        data_dir.mkdir()
    
    return jsonify({'status': 'cleared'})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system stats"""
    data_dir = Path('data')
    
    total_files = 0
    total_size = 0
    
    if data_dir.exists():
        for file_path in data_dir.rglob('*'):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
    
    return jsonify({
        'total_files': total_files,
        'total_size': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'active_tasks': len(active_tasks),
        'completed_tasks': len([t for t in active_tasks.values() if t.status == 'completed'])
    })


if __name__ == '__main__':
    # Ensure data directory exists
    Path('data').mkdir(exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
