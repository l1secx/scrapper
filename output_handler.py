"""
Output Handler Module
Handles saving scraped data in multiple formats
"""

import json
import csv
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

from models import ScrapResult


class OutputHandler:
    """Handle output in multiple formats"""
    
    def __init__(self, output_dir: str, formats: List[str]):
        self.output_dir = Path(output_dir)
        self.formats = formats
        self.logger = logging.getLogger('OutputHandler')
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_results(self, results: List[ScrapResult]):
        """Save results in all specified formats"""
        if not results:
            self.logger.warning("No results to save")
            return
        
        for format_type in self.formats:
            try:
                if format_type == 'json':
                    await self._save_json(results)
                elif format_type == 'csv':
                    await self._save_csv(results)
                elif format_type == 'html':
                    await self._save_html(results)
                elif format_type == 'sqlite':
                    await self._save_sqlite(results)
                else:
                    self.logger.warning(f"Unknown format: {format_type}")
            except Exception as e:
                self.logger.error(f"Failed to save {format_type}: {e}")
    
    async def _save_json(self, results: List[ScrapResult]):
        """Save results as JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = self.output_dir / f"results_{timestamp}.json"
        
        data = [
            {
                'url': r.url,
                'status': r.status,
                'content': r.content,
                'headers': r.headers,
                'timestamp': r.timestamp,
                'size': r.size,
                'content_type': r.content_type,
                'hash': r.hash
            }
            for r in results
        ]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved JSON output to {file_path}")
    
    async def _save_csv(self, results: List[ScrapResult]):
        """Save results as CSV"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = self.output_dir / f"results_{timestamp}.csv"
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Status', 'Timestamp', 'Size', 'Content Type', 'Hash'])
            
            for r in results:
                writer.writerow([
                    r.url,
                    r.status,
                    r.timestamp,
                    r.size,
                    r.content_type,
                    r.hash
                ])
        
        self.logger.info(f"Saved CSV output to {file_path}")
    
    async def _save_html(self, results: List[ScrapResult]):
        """Save results as HTML report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = self.output_dir / f"results_{timestamp}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scraping Results - {timestamp}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .stats {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .result {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #fff;
        }}
        .result.success {{
            border-left: 4px solid #28a745;
        }}
        .result.error {{
            border-left: 4px solid #dc3545;
        }}
        .url {{
            font-weight: bold;
            color: #007bff;
            font-size: 18px;
        }}
        .meta {{
            color: #666;
            font-size: 12px;
            margin: 5px 0;
        }}
        .content {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 3px;
            margin-top: 10px;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 12px;
        }}
        .headers {{
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 3px;
            margin-top: 10px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Scraping Results</h1>
        <div class="stats">
            <strong>Total Results:</strong> {len(results)}<br>
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
"""
        
        for r in results:
            status_class = 'success' if r.status == 200 else 'error'
            html_content += f"""
        <div class="result {status_class}">
            <div class="url">{r.url}</div>
            <div class="meta">
                Status: {r.status} | Size: {r.size} bytes | Type: {r.content_type} | Hash: {r.hash}
            </div>
            <div class="meta">Timestamp: {r.timestamp}</div>
            <div class="headers"><strong>Headers:</strong><br>{json.dumps(r.headers, indent=2)}</div>
            <div class="content"><strong>Content:</strong><br>{r.content[:1000]}{'...' if len(r.content) > 1000 else ''}</div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Saved HTML output to {file_path}")
    
    async def _save_sqlite(self, results: List[ScrapResult]):
        """Save results to SQLite database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = self.output_dir / f"results_{timestamp}.db"
        
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status INTEGER,
                content TEXT,
                headers TEXT,
                timestamp TEXT,
                size INTEGER,
                content_type TEXT,
                hash TEXT
            )
        ''')
        
        # Insert data
        for r in results:
            cursor.execute('''
                INSERT INTO scraped_data (url, status, content, headers, timestamp, size, content_type, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                r.url,
                r.status,
                r.content,
                json.dumps(r.headers),
                r.timestamp,
                r.size,
                r.content_type,
                r.hash
            ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Saved SQLite output to {file_path}")
    
    async def save_single(self, result: ScrapResult, format_type: str = 'json'):
        """Save a single result"""
        await self.save_results([result])
