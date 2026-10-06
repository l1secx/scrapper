#!/usr/bin/env python3
"""
Unified Scraper CLI - Multi-language Web Scraper
Supports Python, Rust, and Go backends
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def get_language_preference():
    """Get language preference from user"""
    print("🚀 Unified Scraper - Multi-language Web Scraper")
    print()
    print("Select backend language:")
    print("1. Python (Feature-rich, production-ready)")
    print("2. Rust (Maximum performance, native compiled)")
    print("3. Go (Fast, concurrent, easy deployment)")
    print("4. Auto (Automatically choose based on availability)")
    print("5. Collaborative (All 3 languages work together!) 🤝")
    print()
    
    choice = input("Enter choice (1-5) [default: 4]: ").strip()
    
    if not choice:
        choice = "4"
    
    return choice


def auto_select_language():
    """Automatically select best available language"""
    # Check if Rust is available
    rust_path = Path("rust-scraper/target/release/turbo-scraper")
    if rust_path.exists():
        return "rust"
    
    # Check if Go is available
    go_path = Path("go-scraper/turbo-scraper")
    if go_path.exists():
        return "go"
    
    # Default to Python
    return "python"


def run_python_scraper(args):
    """Run Python scraper"""
    import asyncio
    from scrap import WebScraper
    from config import Config
    
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
        output_formats=args.output,
        custom_headers=None
    )
    
    async def run():
        async with WebScraper(
            config=config,
            ctf_mode=args.ctf_mode,
            output_dir=args.output_dir,
            data_dir=args.data_dir
        ) as scraper:
            if args.crawl:
                results = await scraper.crawl(
                    start_url=args.crawl,
                    max_depth=args.max_depth,
                    follow_patterns=args.follow_pattern,
                    exclude_patterns=args.exclude_pattern,
                    max_pages=args.max_pages,
                    save_to_file=args.save_files,
                    fetch_resources=args.fetch_resources
                )
            elif args.url:
                result = await scraper.fetch(args.url, save_to_file=args.save_files)
            elif args.url_file:
                with open(args.url_file, 'r') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                await scraper.fetch_multiple(urls, concurrent=True, save_to_file=args.save_files)
            
            stats = scraper.get_stats()
            print_stats(stats)
    
    asyncio.run(run())


def run_rust_scraper(args):
    """Run Rust scraper"""
    rust_path = Path("rust-scraper/target/release/turbo-scraper")
    
    if not rust_path.exists():
        print("Rust scraper not built. Building...")
        subprocess.run(["cargo", "build", "--release"], cwd="rust-scraper", check=True)
    
    cmd = [str(rust_path)]
    
    if args.crawl:
        cmd.extend(["--crawl", args.crawl])
        cmd.extend(["--max-depth", str(args.max_depth)])
        cmd.extend(["--max-pages", str(args.max_pages)])
    elif args.url:
        cmd.extend(["--url", args.url])
    elif args.url_file:
        cmd.extend(["--url-file", args.url_file])
    
    if args.ctf_mode:
        cmd.append("--ctf-mode")
    cmd.extend(["--max-connections", str(args.max_connections)])
    cmd.extend(["--timeout", str(args.timeout)])
    
    if args.no_verify_ssl:
        cmd.append("--no-verify-ssl")
    
    if args.fetch_resources:
        cmd.append("--fetch-resources")
    
    if args.proxy:
        cmd.extend(["--proxy", args.proxy])
    
    if args.verbose:
        cmd.append("--verbose")
    
    subprocess.run(cmd, check=True)


def run_go_scraper(args):
    """Run Go scraper"""
    go_path = Path("go-scraper/turbo-scraper")
    
    if not go_path.exists():
        print("Go scraper not built. Building...")
        subprocess.run(["go", "build", "-o", "turbo-scraper"], cwd="go-scraper", check=True)
    
    cmd = [str(go_path)]
    
    if args.crawl:
        cmd.append(args.crawl)
    elif args.url:
        cmd.append(args.url)
    elif args.url_file:
        cmd.append(args.url_file)
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def run_collaborative_scraper(args):
    """Run collaborative scraper - all 3 languages work together"""
    print("\n" + "="*70)
    print("🤝 COLLABORATIVE MODE - All Languages Working Together")
    print("="*70)
    print("🐍 Python: Orchestration, Rate Limiting, Proxy Management")
    print("🦀 Rust: High-Speed Crawling, Link Extraction")
    print("🐹 Go: Concurrent I/O, File Downloads")
    print("="*70 + "\n")
    
    # Import team_scrape
    import team_scrape
    
    # Get URLs
    urls = []
    if args.url:
        urls = [args.url]
    elif args.url_file:
        with open(args.url_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    elif args.crawl:
        urls = [args.crawl]
    
    if not urls:
        print("No URLs provided")
        return
    
    # If only one URL, expand for collaboration demo
    if len(urls) == 1:
        urls = urls * 9
        print(f"🔄 Expanding to {len(urls)} collaborative tasks\n")
    
    # Run team scrape
    team = team_scrape.TeamScrape()
    results = team.scan(urls)
    
    print(f"\n✅ Collaborative scan complete!")
    print(f"Python, Rust, and Go processed {len(results)} tasks together")


def print_stats(stats):
    """Print statistics"""
    print("\n" + "="*50)
    print("Scraping Statistics")
    print("="*50)
    print(f"Total requests: {stats['total_requests']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Bytes downloaded: {stats['bytes_downloaded']:,}")
    
    if stats['start_time'] and stats['end_time']:
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        print(f"Duration: {duration:.2f} seconds")
        if duration > 0:
            speed = stats['bytes_downloaded'] / duration / 1024
            print(f"Average speed: {speed:.2f} KB/s")
    
    print("\nResources by type:")
    for rtype, count in sorted(stats['resources_by_type'].items()):
        print(f"  {rtype}: {count}")
    print("="*50)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Unified Scraper - Multi-language Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Crawl with Python
  python scraper.py --crawl https://example.com --language python
  
  # Crawl with Rust (maximum speed)
  python scraper.py --crawl https://example.com --language rust
  
  # Crawl with Go
  python scraper.py --crawl https://example.com --language go
  
  # Auto-select language
  python scraper.py --crawl https://example.com

Language Selection:
  python  - Feature-rich, production-ready, rate limiting
  rust    - Maximum performance, native compiled (10-100x faster)
  go      - Fast, concurrent, easy deployment
        '''
    )
    
    # Input options
    parser.add_argument('--url', '-u', help='Single URL to scrape')
    parser.add_argument('--url-file', help='File containing URLs')
    parser.add_argument('--crawl', help='Crawl website starting from URL')
    
    # Crawl options
    parser.add_argument('--max-depth', type=int, default=10, help='Maximum crawl depth')
    parser.add_argument('--max-pages', type=int, default=10000, help='Maximum pages to crawl')
    parser.add_argument('--follow-pattern', action='append', help='URL pattern to follow')
    parser.add_argument('--exclude-pattern', action='append', help='URL pattern to exclude')
    
    # Rate limiting
    parser.add_argument('--ctf-mode', action='store_true', help='CTF mode (no rate limiting)')
    parser.add_argument('--max-requests', type=int, default=10, help='Max requests per time window')
    parser.add_argument('--time-window', type=float, default=1.0, help='Time window in seconds')
    
    # Connection options
    parser.add_argument('--max-connections', type=int, default=500, help='Max concurrent requests')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout')
    parser.add_argument('--no-verify-ssl', action='store_true', help='Disable SSL verification')
    parser.add_argument('--no-redirects', action='store_true', help='Do not follow redirects')
    
    # Retry options
    parser.add_argument('--max-retries', type=int, default=3, help='Max retry attempts')
    parser.add_argument('--retry-delay', type=float, default=1.0, help='Delay between retries')
    
    # Proxy options
    parser.add_argument('--proxy-file', help='Proxy file')
    parser.add_argument('--rotate-proxies', action='store_true', help='Rotate proxies')
    parser.add_argument('--proxy', help='Proxy URL')
    
    # Output options
    parser.add_argument('--output', '-o', nargs='+', choices=['json', 'csv', 'html', 'sqlite'], default=['json'], help='Output format')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    parser.add_argument('--save-files', action='store_true', help='Save files only')
    parser.add_argument('--files-only', action='store_true', help='Only save files, no metadata')
    parser.add_argument('--fetch-resources', action='store_true', default=True, help='Fetch resources')
    
    # Language selection
    parser.add_argument('--language', '-l', choices=['python', 'rust', 'go', 'auto', 'collaborative'], default='auto', help='Backend language')
    parser.add_argument('--no-prompt', action='store_true', help='Skip language selection prompt')
    
    # Other
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Validate input
    if not any([args.url, args.url_file, args.crawl]):
        print("Error: No input specified. Use --url, --url-file, or --crawl")
        sys.exit(1)
    
    # Determine language
    language = args.language
    
    if language == 'auto' and not args.no_prompt:
        choice = get_language_preference()
        language_map = {
            '1': 'python',
            '2': 'rust',
            '3': 'go',
            '4': 'auto',
            '5': 'collaborative'
        }
        language = language_map.get(choice, 'auto')
    
    if language == 'auto':
        language = auto_select_language()
    
    print(f"Using {language.upper()} backend...")
    print()
    
    # Run appropriate scraper
    if language == 'python':
        run_python_scraper(args)
    elif language == 'rust':
        run_rust_scraper(args)
    elif language == 'go':
        run_go_scraper(args)
    elif language == 'collaborative':
        run_collaborative_scraper(args)
    else:
        print(f"Unknown language: {language}")
        sys.exit(1)


if __name__ == '__main__':
    main()
