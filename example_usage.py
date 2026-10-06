#!/usr/bin/env python3
"""
Example usage of the Web Scraper
Demonstrates various features and use cases
"""

import asyncio
from scrap import WebScraper
from config import Config


async def example_single_url():
    """Example: Scrape a single URL"""
    print("Example 1: Single URL Scraping")
    print("-" * 50)
    
    config = Config(max_requests=5, time_window=1.0)
    
    async with WebScraper(config=config) as scraper:
        result = await scraper.fetch('https://httpbin.org/html')
        
        if result:
            print(f"Status: {result.status}")
            print(f"Size: {result.size} bytes")
            print(f"Content-Type: {result.content_type}")
            print(f"Content preview: {result.content[:200]}...")
    
    print()


async def example_multiple_urls():
    """Example: Scrape multiple URLs concurrently"""
    print("Example 2: Multiple URLs (Concurrent)")
    print("-" * 50)
    
    config = Config(max_requests=10, time_window=1.0)
    
    async with WebScraper(config=config) as scraper:
        urls = [
            'https://httpbin.org/html',
            'https://httpbin.org/json',
            'https://httpbin.org/headers',
        ]
        
        results = await scraper.fetch_multiple(urls, concurrent=True)
        
        for result in results:
            print(f"{result.url}: {result.status} ({result.size} bytes)")
    
    print()


async def example_crawl():
    """Example: Crawl a website"""
    print("Example 3: Website Crawling")
    print("-" * 50)
    
    config = Config(max_requests=5, time_window=1.0)
    
    async with WebScraper(config=config) as scraper:
        results = await scraper.crawl(
            start_url='https://httpbin.org',
            max_depth=1,
            max_pages=5
        )
        
        print(f"Crawled {len(results)} pages")
        for result in results:
            print(f"  - {result.url}")
    
    print()


async def example_ctf_mode():
    """Example: CTF mode (unlimited requests)"""
    print("Example 4: CTF Mode (No Rate Limiting)")
    print("-" * 50)
    
    config = Config(max_requests=10, time_window=1.0)
    
    async with WebScraper(config=config, ctf_mode=True) as scraper:
        urls = [f'https://httpbin.org/delay/{i}' for i in range(1, 6)]
        
        results = await scraper.fetch_multiple(urls, concurrent=True)
        
        print(f"Scraped {len(results)} URLs without rate limiting")
        for result in results:
            print(f"  - {result.url}: {result.status}")
    
    print()


async def example_custom_headers():
    """Example: Custom headers"""
    print("Example 5: Custom Headers")
    print("-" * 50)
    
    config = Config(
        max_requests=5,
        time_window=1.0,
        custom_headers={
            'X-Custom-Header': 'MyValue',
            'User-Agent': 'MyCustomBot/1.0'
        }
    )
    
    async with WebScraper(config=config) as scraper:
        result = await scraper.fetch('https://httpbin.org/headers')
        
        if result:
            print(f"Status: {result.status}")
            print(f"Sent custom headers successfully")
    
    print()


async def example_statistics():
    """Example: Get scraping statistics"""
    print("Example 6: Statistics")
    print("-" * 50)
    
    config = Config(max_requests=5, time_window=1.0)
    
    async with WebScraper(config=config) as scraper:
        urls = [
            'https://httpbin.org/html',
            'https://httpbin.org/json',
            'https://httpbin.org/headers',
        ]
        
        await scraper.fetch_multiple(urls)
        
        stats = scraper.get_stats()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Bytes downloaded: {stats['bytes_downloaded']}")
    
    print()


async def main():
    """Run all examples"""
    print("=" * 50)
    print("Web Scraper Examples")
    print("=" * 50)
    print()
    
    await example_single_url()
    await example_multiple_urls()
    await example_crawl()
    await example_ctf_mode()
    await example_custom_headers()
    await example_statistics()
    
    print("=" * 50)
    print("Examples completed!")
    print("=" * 50)


if __name__ == '__main__':
    asyncio.run(main())
