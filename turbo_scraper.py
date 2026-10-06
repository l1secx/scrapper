#!/usr/bin/env python3
"""
Turbo Scraper - Ultra High Performance Web Scraper
Optimized with multiprocessing, threading, and connection pooling
"""

import asyncio
import aiohttp
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import hashlib
import re
from typing import Optional, Dict, List, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import argparse
import sys
from tqdm import tqdm
import signal
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedResource:
    url: str
    status: int
    size: int
    content_type: str
    resource_type: str
    timestamp: str


class TurboScraper:
    """Ultra high performance web scraper with advanced optimizations"""
    
    def __init__(
        self,
        max_connections: int = 500,
        timeout: int = 30,
        verify_ssl: bool = True,
        output_dir: str = "data",
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        proxy: Optional[str] = None,
        follow_redirects: bool = True
    ):
        self.max_connections = max_connections
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.output_dir = Path(output_dir)
        self.user_agent = user_agent
        self.proxy = proxy
        self.follow_redirects = follow_redirects
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.visited: Set[str] = set()
        self.stats = {
            'total_requests': 0,
            'successful': 0,
            'failed': 0,
            'bytes_downloaded': 0,
            'resources_by_type': defaultdict(int),
            'start_time': None,
            'end_time': None
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 2)
        
        # Pre-compile regex patterns
        self.js_pattern = re.compile(r'\.js$', re.IGNORECASE)
        self.css_pattern = re.compile(r'\.css$', re.IGNORECASE)
        self.img_pattern = re.compile(r'\.(png|jpg|jpeg|gif|svg|webp|ico)$', re.IGNORECASE)
        self.font_pattern = re.compile(r'\.(woff|woff2|ttf|otf|eot)$', re.IGNORECASE)
        self.php_pattern = re.compile(r'\.php$', re.IGNORECASE)
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=100,
            ssl=self.verify_ssl,
            force_close=False,
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._get_headers(),
            raise_for_status=False
        )
        
        self.stats['start_time'] = datetime.now()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=False)
        
        self.stats['end_time'] = datetime.now()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
    def get_site_name(self, url: str) -> str:
        """Extract site name from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain.replace('.', '_')
    
    def get_resource_type(self, url: str, content_type: str) -> str:
        """Determine resource type"""
        url_lower = url.lower()
        ct_lower = content_type.lower()
        
        if 'javascript' in ct_lower or 'js' in ct_lower or self.js_pattern.search(url_lower):
            return 'js'
        elif 'css' in ct_lower or self.css_pattern.search(url_lower):
            return 'css'
        elif 'image' in ct_lower or self.img_pattern.search(url_lower):
            return 'images'
        elif 'font' in ct_lower or self.font_pattern.search(url_lower):
            return 'fonts'
        elif 'html' in ct_lower or url_lower.endswith(('.html', '.htm')):
            return 'html'
        elif 'php' in ct_lower or self.php_pattern.search(url_lower):
            return 'php'
        elif 'json' in ct_lower or url_lower.endswith('.json'):
            return 'json'
        elif 'xml' in ct_lower or url_lower.endswith('.xml'):
            return 'xml'
        else:
            return 'other'
    
    def get_file_path(self, url: str, resource_type: str, content_type: str) -> Path:
        """Get file path for saving resource"""
        site_name = self.get_site_name(url)
        type_dir = self.output_dir / site_name / resource_type
        type_dir.mkdir(parents=True, exist_ok=True)
        
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path or path == '/':
            filename = f"index{self.get_extension(content_type)}"
        else:
            clean_path = path.replace('/', '_').replace('\\', '_')
            filename = clean_path.split('?')[0]
            
            if not filename or '.' not in filename:
                filename += self.get_extension(content_type)
        
        # Limit filename length
        if len(filename) > 200:
            filename = filename[:180] + self.get_extension(content_type)
        
        return type_dir / filename
    
    def get_extension(self, content_type: str) -> str:
        """Get file extension from content type"""
        ct_lower = content_type.lower()
        extensions = {
            'text/html': '.html',
            'application/json': '.json',
            'text/css': '.css',
            'application/javascript': '.js',
            'text/javascript': '.js',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/svg+xml': '.svg',
            'image/webp': '.webp',
            'font/woff': '.woff',
            'font/woff2': '.woff2',
            'font/ttf': '.ttf',
            'application/php': '.php',
            'text/xml': '.xml',
        }
        
        for ct, ext in extensions.items():
            if ct in ct_lower:
                return ext
        
        return '.txt'
    
    async def fetch_url(self, url: str, pb: Optional[tqdm] = None) -> Optional[ScrapedResource]:
        """Fetch a single URL with optimized connection handling"""
        try:
            async with self.session.get(url) as response:
                status = response.status
                content_type = response.headers.get('Content-Type', 'text/plain')
                
                if status == 200:
                    content = await response.read()
                    size = len(content)
                    
                    # Save to file in thread pool to avoid blocking
                    resource_type = self.get_resource_type(url, content_type)
                    file_path = self.get_file_path(url, resource_type, content_type)
                    
                    # Write in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        self.executor,
                        self._save_file,
                        file_path,
                        content
                    )
                    
                    # Update stats
                    self.stats['total_requests'] += 1
                    self.stats['successful'] += 1
                    self.stats['bytes_downloaded'] += size
                    self.stats['resources_by_type'][resource_type] += 1
                    
                    if pb:
                        pb.update(1)
                    
                    return ScrapedResource(
                        url=url,
                        status=status,
                        size=size,
                        content_type=content_type,
                        resource_type=resource_type,
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    self.stats['total_requests'] += 1
                    self.stats['failed'] += 1
                    
                    if pb:
                        pb.update(1)
                    
                    logger.warning(f"Failed to fetch {url}: {status}")
                    return None
                    
        except Exception as e:
            self.stats['total_requests'] += 1
            self.stats['failed'] += 1
            
            if pb:
                pb.update(1)
            
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _save_file(self, file_path: Path, content: bytes):
        """Save file synchronously (called from thread pool)"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(content)
    
    def extract_resources(self, html: str, base_url: str) -> List[Tuple[str, str]]:
        """Extract all resources from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        resources = []
        
        # JS
        for script in soup.find_all('script', src=True):
            src = script['src']
            full_url = urljoin(base_url, src)
            resources.append((full_url, 'js'))
        
        # CSS
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                resources.append((full_url, 'css'))
        
        # Images
        for img in soup.find_all('img', src=True):
            src = img['src']
            full_url = urljoin(base_url, src)
            resources.append((full_url, 'images'))
        
        # Links
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(base_url, href)
            resources.append((full_url, 'html'))
        
        return resources
    
    async def crawl(
        self,
        start_url: str,
        max_depth: int = 10,
        max_pages: int = 10000,
        fetch_resources: bool = True
    ):
        """Crawl website with optimized BFS traversal"""
        base_url = urlparse(start_url)
        base_domain = base_url.netloc
        
        to_visit: List[Tuple[str, int]] = [(start_url, 0)]
        resources_to_fetch: List[str] = []
        visited_count = 0
        
        pb = tqdm(total=max_pages, desc="Crawling", unit="pages")
        
        while to_visit and visited_count < max_pages:
            # Process in batches for better concurrency
            batch = to_visit[:self.max_connections]
            to_visit = to_visit[self.max_connections:]
            
            # Filter already visited
            batch = [(url, depth) for url, depth in batch if url not in self.visited]
            
            if not batch:
                continue
            
            # Mark as visited
            for url, _ in batch:
                self.visited.add(url)
            
            # Fetch batch concurrently
            tasks = [self.fetch_url(url, pb) for url, _ in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result, (url, depth) in zip(results, batch):
                if isinstance(result, ScrapedResource) and result.status == 200:
                    visited_count += 1
                    
                    if fetch_resources and result.resource_type == 'html':
                        # Extract resources from HTML
                        file_path = self.get_file_path(url, 'html', result.content_type)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                html_content = f.read()
                            
                            extracted = self.extract_resources(html_content, url)
                            for res_url, res_type in extracted:
                                if res_url not in self.visited:
                                    # Check same domain
                                    res_domain = urlparse(res_url).netloc
                                    if res_domain == base_domain:
                                        if depth < max_depth:
                                            to_visit.append((res_url, depth + 1))
                                        else:
                                            resources_to_fetch.append(res_url)
                        except Exception as e:
                            logger.error(f"Error reading HTML {url}: {e}")
        
        # Fetch remaining resources
        if resources_to_fetch:
            pb.total = len(resources_to_fetch) + visited_count
            pb.set_description("Fetching resources")
            
            # Remove duplicates
            resources_to_fetch = list(set(resources_to_fetch) - self.visited)
            
            # Fetch in batches
            for i in range(0, len(resources_to_fetch), self.max_connections):
                batch = resources_to_fetch[i:i + self.max_connections]
                tasks = [self.fetch_url(url, pb) for url in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
        
        pb.close()
    
    async def fetch_multiple(self, urls: List[str]):
        """Fetch multiple URLs concurrently"""
        pb = tqdm(total=len(urls), desc="Fetching", unit="urls")
        
        # Remove duplicates
        urls = list(set(urls))
        
        # Fetch in batches
        for i in range(0, len(urls), self.max_connections):
            batch = urls[i:i + self.max_connections]
            tasks = [self.fetch_url(url, pb) for url in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        pb.close()
    
    def print_stats(self):
        """Print scraping statistics"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*50)
        print("Turbo Scraper Statistics")
        print("="*50)
        print(f"Total requests: {self.stats['total_requests']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Bytes downloaded: {self.stats['bytes_downloaded']:,}")
        
        if duration:
            print(f"Duration: {duration:.2f} seconds")
            if duration > 0:
                speed = self.stats['bytes_downloaded'] / duration / 1024
                print(f"Average speed: {speed:.2f} KB/s")
        
        print("\nResources by type:")
        for rtype, count in sorted(self.stats['resources_by_type'].items()):
            print(f"  {rtype}: {count}")
        print("="*50)


def main():
    parser = argparse.ArgumentParser(description='Turbo Scraper - Ultra High Performance Web Scraper')
    
    parser.add_argument('--url', help='Single URL to scrape')
    parser.add_argument('--url-file', help='File containing URLs')
    parser.add_argument('--crawl', help='Crawl website starting from URL')
    parser.add_argument('--max-depth', type=int, default=10, help='Maximum crawl depth')
    parser.add_argument('--max-pages', type=int, default=10000, help='Maximum pages to crawl')
    parser.add_argument('--max-connections', type=int, default=500, help='Max concurrent requests')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout')
    parser.add_argument('--no-verify-ssl', action='store_true', help='Disable SSL verification')
    parser.add_argument('--output-dir', default='data', help='Output directory')
    parser.add_argument('--fetch-resources', action='store_true', default=True, help='Fetch resources')
    parser.add_argument('--no-fetch-resources', action='store_false', dest='fetch_resources', help='Do not fetch resources')
    parser.add_argument('--proxy', help='Proxy URL')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🚀 Turbo Scraper - Ultra High Performance Web Scraper")
    print()
    
    async def run():
        scraper = TurboScraper(
            max_connections=args.max_connections,
            timeout=args.timeout,
            verify_ssl=not args.no_verify_ssl,
            output_dir=args.output_dir,
            proxy=args.proxy
        )
        
        async with scraper:
            if args.crawl:
                print(f"Crawling {args.crawl} (max depth: {args.max_depth}, max pages: {args.max_pages})")
                await scraper.crawl(
                    start_url=args.crawl,
                    max_depth=args.max_depth,
                    max_pages=args.max_pages,
                    fetch_resources=args.fetch_resources
                )
            elif args.url:
                print(f"Fetching {args.url}")
                await scraper.fetch_url(args.url)
            elif args.url_file:
                with open(args.url_file, 'r') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                print(f"Fetching {len(urls)} URLs from file")
                await scraper.fetch_multiple(urls)
            
            scraper.print_stats()
    
    asyncio.run(run())


if __name__ == '__main__':
    main()
