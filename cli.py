#!/usr/bin/env python3
"""
CLI Interface for Web Scraper
Professional command-line interface with extensive options
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

from scrap import WebScraper
from config import Config


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Professional Web Scraper - Production-ready scraping tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Simple scraping
  python cli.py --url https://example.com
  
  # CTF mode (no rate limiting)
  python cli.py --url https://ctf.example.com --ctf-mode
  
  # Scrape multiple URLs
  python cli.py --urls https://site1.com https://site2.com https://site3.com
  
  # Crawl website
  python cli.py --crawl https://example.com --max-depth 3 --max-pages 50
  
  # With proxy rotation
  python cli.py --url https://example.com --proxy-file proxies.txt --rotate-proxies
  
  # Multiple output formats
  python cli.py --url https://example.com --output json csv html sqlite
  
  # Custom rate limiting
  python cli.py --url https://example.com --max-requests 5 --time-window 2
  
  # With custom headers
  python cli.py --url https://example.com --header "Authorization: Bearer token"
  
  # Read URLs from file
  python cli.py --url-file urls.txt --output json csv
        '''
    )
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_group.add_argument(
        '--url', '-u',
        type=str,
        help='Single URL to scrape'
    )
    input_group.add_argument(
        '--urls',
        type=str,
        nargs='+',
        help='Multiple URLs to scrape'
    )
    input_group.add_argument(
        '--url-file',
        type=str,
        help='File containing URLs (one per line)'
    )
    input_group.add_argument(
        '--crawl',
        type=str,
        help='Crawl website starting from this URL'
    )
    
    # Crawl options
    crawl_group = parser.add_argument_group('Crawl Options')
    crawl_group.add_argument(
        '--max-depth',
        type=int,
        default=1,
        help='Maximum crawl depth (default: 1)'
    )
    crawl_group.add_argument(
        '--max-pages',
        type=int,
        default=100,
        help='Maximum pages to crawl (default: 100)'
    )
    crawl_group.add_argument(
        '--follow-pattern',
        type=str,
        action='append',
        help='URL pattern to follow (regex, can be used multiple times)'
    )
    crawl_group.add_argument(
        '--exclude-pattern',
        type=str,
        action='append',
        help='URL pattern to exclude (regex, can be used multiple times)'
    )
    crawl_group.add_argument(
        '--fetch-resources',
        action='store_true',
        default=True,
        help='Fetch JS, CSS, images, fonts, etc. (default: True)'
    )
    crawl_group.add_argument(
        '--no-fetch-resources',
        action='store_false',
        dest='fetch_resources',
        help='Do not fetch resources (JS, CSS, images, etc.)'
    )
    
    # Rate limiting
    rate_group = parser.add_argument_group('Rate Limiting')
    rate_group.add_argument(
        '--ctf-mode',
        action='store_true',
        help='CTF mode - disable rate limiting (unlimited requests)'
    )
    rate_group.add_argument(
        '--max-requests',
        type=int,
        default=10,
        help='Maximum requests per time window (default: 10)'
    )
    rate_group.add_argument(
        '--time-window',
        type=float,
        default=1.0,
        help='Time window in seconds (default: 1.0)'
    )
    
    # Connection options
    conn_group = parser.add_argument_group('Connection Options')
    conn_group.add_argument(
        '--max-connections',
        type=int,
        default=100,
        help='Maximum concurrent connections (default: 100)'
    )
    conn_group.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )
    conn_group.add_argument(
        '--no-verify-ssl',
        action='store_true',
        help='Disable SSL certificate verification'
    )
    conn_group.add_argument(
        '--no-redirects',
        action='store_true',
        help='Do not follow redirects'
    )
    
    # Retry options
    retry_group = parser.add_argument_group('Retry Options')
    retry_group.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts (default: 3)'
    )
    retry_group.add_argument(
        '--retry-delay',
        type=float,
        default=1.0,
        help='Delay between retries in seconds (default: 1.0)'
    )
    
    # Proxy options
    proxy_group = parser.add_argument_group('Proxy Options')
    proxy_group.add_argument(
        '--proxy-file',
        type=str,
        help='File containing proxies (one per line)'
    )
    proxy_group.add_argument(
        '--rotate-proxies',
        action='store_true',
        help='Rotate through proxies automatically'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output',
        '-o',
        type=str,
        nargs='+',
        choices=['json', 'csv', 'html', 'sqlite'],
        default=['json'],
        help='Output format(s) (default: json)'
    )
    output_group.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory (default: output)'
    )
    output_group.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Data directory for downloaded files (default: data)'
    )
    output_group.add_argument(
        '--save-files',
        action='store_true',
        help='Save scraped content to files'
    )
    output_group.add_argument(
        '--files-only',
        action='store_true',
        help='Only save files, no JSON/CSV/HTML/SQLite output'
    )
    
    # Headers
    header_group = parser.add_argument_group('Headers')
    header_group.add_argument(
        '--header',
        type=str,
        action='append',
        help='Custom header (format: "Name: Value", can be used multiple times)'
    )
    
    # Other options
    other_group = parser.add_argument_group('Other Options')
    other_group.add_argument(
        '--concurrent',
        action='store_true',
        default=True,
        help='Fetch URLs concurrently (default: True)'
    )
    other_group.add_argument(
        '--no-concurrent',
        action='store_false',
        dest='concurrent',
        help='Fetch URLs sequentially'
    )
    other_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def parse_headers(header_list: List[str]) -> dict:
    """Parse custom headers from command line"""
    headers = {}
    for h in header_list:
        if ':' in h:
            name, value = h.split(':', 1)
            headers[name.strip()] = value.strip()
    return headers


def read_urls_from_file(file_path: str) -> List[str]:
    """Read URLs from file"""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: URL file not found: {file_path}")
        sys.exit(1)
    
    urls = []
    with open(path, 'r') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):
                urls.append(url)
    
    return urls


async def main():
    """Main entry point"""
    args = parse_args()
    
    # Validate input
    if not any([args.url, args.urls, args.url_file, args.crawl]):
        print("Error: No input specified. Use --url, --urls, --url-file, or --crawl")
        sys.exit(1)
    
    # Prepare custom headers
    custom_headers = None
    if args.header:
        custom_headers = parse_headers(args.header)
    
    # Handle files-only mode
    if args.files_only:
        output_formats = []
        save_files = True
    else:
        output_formats = args.output
        save_files = args.save_files
    
    # Create config
    config = Config(
        max_requests=args.max_requests,
        time_window=args.time_window,
        max_connections=args.max_connections,
        timeout=args.timeout,
        verify_ssl=not args.no_verify_ssl,
        follow_redirects=not args.no_redirects,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        proxy_file=args.proxy_file,
        rotate_proxies=args.rotate_proxies,
        output_formats=output_formats,
        custom_headers=custom_headers
    )
    
    # Collect URLs
    urls = []
    if args.url:
        urls.append(args.url)
    if args.urls:
        urls.extend(args.urls)
    if args.url_file:
        urls.extend(read_urls_from_file(args.url_file))
    
    # Run scraper
    async with WebScraper(
        config=config,
        ctf_mode=args.ctf_mode,
        output_dir=args.output_dir,
        data_dir=args.data_dir
    ) as scraper:
        
        try:
            if args.crawl:
                # Crawl mode
                print(f"Crawling {args.crawl} (max depth: {args.max_depth}, max pages: {args.max_pages})")
                results = await scraper.crawl(
                    start_url=args.crawl,
                    max_depth=args.max_depth,
                    follow_patterns=args.follow_pattern,
                    exclude_patterns=args.exclude_pattern,
                    max_pages=args.max_pages,
                    save_to_file=save_files,
                    fetch_resources=args.fetch_resources
                )
            elif urls:
                # Fetch mode
                if len(urls) == 1:
                    print(f"Fetching {urls[0]}")
                    result = await scraper.fetch(urls[0], save_to_file=save_files)
                    results = [result] if result else []
                else:
                    print(f"Fetching {len(urls)} URLs (concurrent: {args.concurrent})")
                    results = await scraper.fetch_multiple(
                        urls=urls,
                        concurrent=args.concurrent,
                        save_to_file=save_files
                    )
            else:
                results = []
            
            # Print stats
            stats = scraper.get_stats()
            print("\n" + "="*50)
            print("Scraping Statistics:")
            print("="*50)
            print(f"Total requests: {stats['total_requests']}")
            print(f"Successful: {stats['successful']}")
            print(f"Failed: {stats['failed']}")
            print(f"Bytes downloaded: {stats['bytes_downloaded']:,}")
            
            if stats['start_time'] and stats['end_time']:
                duration = (stats['end_time'] - stats['start_time']).total_seconds()
                print(f"Duration: {duration:.2f} seconds")
                if duration > 0:
                    print(f"Average speed: {stats['bytes_downloaded'] / duration / 1024:.2f} KB/s")
            
            print(f"\nResults saved to: {args.output_dir}/")
            if args.save_files:
                print(f"Data files saved to: {args.data_dir}/")
            
            if args.verbose:
                print("\nDetailed results:")
                for r in results:
                    print(f"  - {r.url}: {r.status} ({r.size} bytes)")
            
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
