#!/usr/bin/env python3
"""
Professional Web Scraper
A production-ready web scraper with rate limiting, proxy support, and multiple output formats.
"""

import asyncio
import aiohttp
import time
import random
import json
import logging
from typing import Optional, Dict, List, Any, Set
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime
import hashlib

from rate_limiter import RateLimiter
from proxy_manager import ProxyManager
from output_handler import OutputHandler
from config import Config
from models import ScrapResult


class WebScraper:
    """Professional web scraper with advanced features"""

    def __init__(
        self,
        config: Config,
        ctf_mode: bool = False,
        output_dir: str = "output",
        data_dir: str = "data"
    ):
        self.config = config
        self.ctf_mode = ctf_mode
        self.output_dir = Path(output_dir)
        self.data_dir = Path(data_dir)
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.rate_limiter = RateLimiter(
            max_requests=config.max_requests,
            time_window=config.time_window,
            ctf_mode=ctf_mode
        )
        self.proxy_manager = ProxyManager(
            proxy_file=config.proxy_file,
            rotate_proxies=config.rotate_proxies
        )
        self.output_handler = OutputHandler(
            output_dir=str(self.output_dir),
            formats=config.output_formats
        )
        
        # Setup logging
        self._setup_logging()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful': 0,
            'failed': 0,
            'bytes_downloaded': 0,
            'start_time': None,
            'end_time': None
        }
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        # Session setup
        self.session: Optional[aiohttp.ClientSession] = None
        self.visited_urls: Set[str] = set()
        self.scraped_data: List[ScrapResult] = []

    def _setup_logging(self):
        """Setup logging configuration"""
        log_file = self.output_dir / "scraper.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('WebScraper')

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            ssl=self.config.verify_ssl
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._get_headers()
        )
        
        await self.proxy_manager.load_proxies()
        self.stats['start_time'] = datetime.now()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        
        self.stats['end_time'] = datetime.now()
        await self._finalize()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)
        
        return headers

    async def fetch(
        self,
        url: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        save_to_file: bool = False,
        file_path: Optional[str] = None
    ) -> Optional[ScrapResult]:
        """
        Fetch a URL with rate limiting and retry logic
        
        Args:
            url: URL to fetch
            method: HTTP method
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Custom headers
            save_to_file: Whether to save response to file
            file_path: Custom file path for saving
            
        Returns:
            ScrapResult or None if failed
        """
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Get proxy if available
        proxy = await self.proxy_manager.get_proxy()
        
        # Prepare headers
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        # Retry logic
        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(f"Fetching {url} (attempt {attempt + 1}/{self.config.max_retries})")
                self.stats['total_requests'] += 1
                
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    proxy=proxy,
                    allow_redirects=self.config.follow_redirects
                ) as response:
                    content = await response.text()
                    
                    result = ScrapResult(
                        url=url,
                        status=response.status,
                        content=content,
                        headers=dict(response.headers),
                        timestamp=datetime.now().isoformat(),
                        size=len(content),
                        content_type=response.headers.get('Content-Type', 'unknown')
                    )
                    
                    # Update stats
                    if response.status == 200:
                        self.stats['successful'] += 1
                        self.stats['bytes_downloaded'] += len(content)
                    else:
                        self.stats['failed'] += 1
                    
                    # Save to file if requested
                    if save_to_file:
                        await self._save_to_file(result, file_path)
                    
                    # Add to scraped data
                    self.scraped_data.append(result)
                    
                    # Mark URL as visited
                    self.visited_urls.add(url)
                    
                    # Report proxy success/failure
                    if proxy:
                        await self.proxy_manager.report_success(proxy)
                    
                    return result
                    
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout fetching {url}")
                if proxy:
                    await self.proxy_manager.report_failure(proxy)
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                
            except aiohttp.ClientError as e:
                self.logger.error(f"Client error fetching {url}: {e}")
                if proxy:
                    await self.proxy_manager.report_failure(proxy)
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                
            except Exception as e:
                self.logger.error(f"Unexpected error fetching {url}: {e}")
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        self.logger.error(f"Failed to fetch {url} after {self.config.max_retries} attempts")
        self.stats['failed'] += 1
        return None

    async def _save_to_file(self, result: ScrapResult, custom_path: Optional[str] = None):
        """Save scraped content to file"""
        if custom_path:
            file_path = Path(custom_path)
        else:
            # Generate filename from URL
            url_hash = hashlib.md5(result.url.encode()).hexdigest()[:16]
            ext = self._get_extension(result.content_type)
            file_path = self.data_dir / f"{url_hash}{ext}"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result.content)
        
        self.logger.info(f"Saved content to {file_path}")

    def _get_extension(self, content_type: str) -> str:
        """Get file extension from content type"""
        extensions = {
            'text/html': '.html',
            'application/json': '.json',
            'text/xml': '.xml',
            'application/xml': '.xml',
            'text/plain': '.txt',
            'application/pdf': '.pdf',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
        }
        
        for ct, ext in extensions.items():
            if ct in content_type:
                return ext
        
        return '.txt'

    async def fetch_multiple(
        self,
        urls: List[str],
        concurrent: bool = True,
        save_to_file: bool = False
    ) -> List[ScrapResult]:
        """
        Fetch multiple URLs
        
        Args:
            urls: List of URLs to fetch
            concurrent: Whether to fetch concurrently
            save_to_file: Whether to save responses to files
            
        Returns:
            List of ScrapResults
        """
        if concurrent:
            tasks = [self.fetch(url, save_to_file=save_to_file) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and None values
            valid_results = [r for r in results if isinstance(r, ScrapResult)]
            return valid_results
        else:
            results = []
            for url in urls:
                result = await self.fetch(url, save_to_file=save_to_file)
                if result:
                    results.append(result)
            return results

    async def crawl(
        self,
        start_url: str,
        max_depth: int = 1,
        follow_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_pages: int = 100
    ) -> List[ScrapResult]:
        """
        Crawl website starting from start_url
        
        Args:
            start_url: Starting URL
            max_depth: Maximum crawl depth
            follow_patterns: URL patterns to follow (regex)
            exclude_patterns: URL patterns to exclude (regex)
            max_pages: Maximum pages to crawl
            
        Returns:
            List of ScrapResults
        """
        import re
        
        results = []
        to_visit = [(start_url, 0)]
        visited_count = 0
        
        while to_visit and visited_count < max_pages:
            url, depth = to_visit.pop(0)
            
            if url in self.visited_urls:
                continue
            
            if depth > max_depth:
                continue
            
            result = await self.fetch(url)
            if not result:
                continue
            
            results.append(result)
            visited_count += 1
            
            # Extract links if not at max depth
            if depth < max_depth:
                links = self._extract_links(result.content, url)
                
                for link in links:
                    # Apply follow patterns
                    if follow_patterns:
                        if not any(re.search(pattern, link) for pattern in follow_patterns):
                            continue
                    
                    # Apply exclude patterns
                    if exclude_patterns:
                        if any(re.search(pattern, link) for pattern in exclude_patterns):
                            continue
                    
                    if link not in self.visited_urls:
                        to_visit.append((link, depth + 1))
        
        return results

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract links from HTML"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(base_url, href)
            
            # Only include same domain links
            if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                links.append(absolute_url)
        
        return links

    async def _finalize(self):
        """Finalize scraping - save outputs and stats"""
        # Save scraped data
        await self.output_handler.save_results(self.scraped_data)
        
        # Save statistics
        stats_file = self.output_dir / "stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        
        self.logger.info(f"Scraping complete. Stats: {self.stats}")

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return self.stats.copy()
