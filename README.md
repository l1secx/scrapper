# Professional Web Scraper - Multi-Language

A production-ready, feature-rich web scraper with **Python**, **Rust**, and **Go** backends. Advanced rate limiting, proxy support, and multiple output formats. Designed for both CTF competitions (unlimited mode) and professional penetration testing (controlled rate limiting).

## 🚀 Quick Start

### Unified CLI (Recommended)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build all scrapers (optional)
make build

# Run with auto-selected language
python scraper.py --crawl https://example.com

# Or specify language explicitly
python scraper.py --crawl https://example.com --language python  # Feature-rich
python scraper.py --crawl https://example.com --language rust    # Maximum speed
python scraper.py --crawl https://example.com --language go      # Fast & concurrent
```

### Language Comparison

| Feature | Python | Rust | Go |
|---------|--------|------|-----|
| **Speed** | Baseline | 10-100x faster | 5-50x faster |
| **Features** | Most features | High performance | Fast & concurrent |
| **Ease of Use** | Easiest | Requires build | Requires build |
| **Rate Limiting** | ✅ Full support | ❌ CTF mode only | ❌ CTF mode only |
| **Proxy** | ✅ Rotation | ✅ Basic | ❌ None |

See [UNIFIED.md](UNIFIED.md) for detailed multi-language documentation.

## Features

### Core Features
- **Async/Await Architecture**: High-performance asynchronous scraping with aiohttp
- **Rate Limiting**: Token bucket algorithm with configurable limits
- **CTF Mode**: Unlimited requests for CTF competitions
- **Proxy Support**: Proxy rotation with health checking
- **Multiple Output Formats**: JSON, CSV, HTML, SQLite
- **Automatic Retry**: Configurable retry logic with exponential backoff
- **Web Crawling**: Recursive website crawling with depth control
- **URL Pattern Matching**: Include/exclude URLs using regex patterns
- **Custom Headers**: Add custom HTTP headers
- **File Downloads**: Save scraped content to files
- **Statistics**: Detailed scraping statistics and logs

### Advanced Features
- Connection pooling and reuse
- SSL verification control
- Redirect following control
- Concurrent request processing
- Content hashing for deduplication
- HTML link extraction
- User agent rotation
- Proxy health monitoring
- Graceful error handling

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build Rust scraper (optional, for maximum performance)
cd rust-scraper
cargo build --release
cd ..

# Build Go scraper (optional)
cd go-scraper
go build -o turbo-scraper
cd ..

# Or build all at once
make build
```

## Project Structure

```
scrapper/
├── scraper.py              # Unified CLI (main entry point)
├── cli.py                  # Python CLI (standalone)
├── scrap.py                 # Python scraper core
├── config.py                # Python configuration
├── models.py                # Python data models
├── rate_limiter.py          # Python rate limiter
├── proxy_manager.py          # Python proxy manager
├── output_handler.py        # Python output handler
├── turbo_scraper.py         # Python turbo scraper
├── rust-scraper/            # Rust implementation
│   ├── Cargo.toml
│   └── src/main.rs
└── go-scraper/              # Go implementation
    ├── go.mod
    └── main.go
```

## Quick Start

### Unified CLI Usage

```bash
# Scrape a single URL (auto-selects language)
python scraper.py --url https://example.com

# Crawl website with Python backend
python scraper.py --crawl https://example.com --language python --max-depth 2

# Crawl with Rust backend (maximum speed)
python scraper.py --crawl https://example.com --language rust --max-depth 3 --max-pages 100

# Crawl with Go backend
python scraper.py --crawl https://example.com --language go

# CTF mode (unlimited, Python)
python scraper.py --url https://ctf.example.com --language python --ctf-mode
```

### Standalone Python CLI

```bash
# Scrape a single URL
python cli.py --url https://example.com

# CTF mode (no rate limiting)
python cli.py --url https://ctf.example.com --ctf-mode

# Scrape multiple URLs
python cli.py --urls https://site1.com https://site2.com https://site3.com

# Read URLs from file
python cli.py --url-file urls.txt
```

### Web Crawling

```bash
# Crawl website with depth 2 (unified CLI)
python scraper.py --crawl https://example.com --max-depth 2

# Crawl with max pages limit (Python standalone)
python cli.py --crawl https://example.com --max-depth 3 --max-pages 100

# Crawl with URL patterns
python cli.py --crawl https://example.com --follow-pattern "/api/" --exclude-pattern "/admin/"
```

### Rate Limiting

```bash
# Custom rate limit (5 requests per 2 seconds)
python cli.py --url https://example.com --max-requests 5 --time-window 2

# CTF mode (unlimited)
python cli.py --url https://example.com --ctf-mode
```

### Proxy Support

```bash
# Use single proxy
python cli.py --url https://example.com --proxy-file proxies.txt

# Rotate through proxies
python cli.py --url https://example.com --proxy-file proxies.txt --rotate-proxies
```

### Output Options

```bash
# Multiple output formats
python cli.py --url https://example.com --output json csv html sqlite

# Custom output directory
python cli.py --url https://example.com --output-dir my_results

# Save scraped content to files
python cli.py --url https://example.com --save-files
```

### Custom Headers

```bash
# Add custom header
python cli.py --url https://example.com --header "Authorization: Bearer token"

# Multiple headers
python cli.py --url https://example.com --header "Authorization: Bearer token" --header "X-Custom: value"
```

## Command Line Options

### Input Options
- `--url, -u`: Single URL to scrape
- `--urls`: Multiple URLs to scrape
- `--url-file`: File containing URLs (one per line)
- `--crawl`: Crawl website starting from this URL

### Crawl Options
- `--max-depth`: Maximum crawl depth (default: 1)
- `--max-pages`: Maximum pages to crawl (default: 100)
- `--follow-pattern`: URL pattern to follow (regex)
- `--exclude-pattern`: URL pattern to exclude (regex)

### Rate Limiting
- `--ctf-mode`: Disable rate limiting (unlimited requests)
- `--max-requests`: Maximum requests per time window (default: 10)
- `--time-window`: Time window in seconds (default: 1.0)

### Connection Options
- `--max-connections`: Maximum concurrent connections (default: 100)
- `--timeout`: Request timeout in seconds (default: 30)
- `--no-verify-ssl`: Disable SSL certificate verification
- `--no-redirects`: Do not follow redirects

### Retry Options
- `--max-retries`: Maximum retry attempts (default: 3)
- `--retry-delay`: Delay between retries in seconds (default: 1.0)

### Proxy Options
- `--proxy-file`: File containing proxies (one per line)
- `--rotate-proxies`: Rotate through proxies automatically

### Output Options
- `--output, -o`: Output format(s) - json, csv, html, sqlite (default: json)
- `--output-dir`: Output directory (default: output)
- `--data-dir`: Data directory for downloaded files (default: data)
- `--save-files`: Save scraped content to files

### Headers
- `--header`: Custom header (format: "Name: Value")

### Other Options
- `--concurrent`: Fetch URLs concurrently (default: True)
- `--no-concurrent`: Fetch URLs sequentially
- `--verbose, -v`: Enable verbose output

## Proxy File Format

Create a `proxies.txt` file with one proxy per line:

```
http://proxy1.example.com:8080
http://user:pass@proxy2.example.com:8080
socks5://proxy3.example.com:1080
```

## URL File Format

Create a `urls.txt` file with one URL per line:

```
https://example.com/page1
https://example.com/page2
https://example.com/api/endpoint
```

## Output Formats

### JSON
Structured JSON with all response data:
```json
[
  {
    "url": "https://example.com",
    "status": 200,
    "content": "...",
    "headers": {...},
    "timestamp": "2024-01-01T12:00:00",
    "size": 1234,
    "content_type": "text/html",
    "hash": "abc123..."
  }
]
```

### CSV
Tabular format with key fields:
```
URL,Status,Timestamp,Size,Content Type,Hash
https://example.com,200,2024-01-01T12:00:00,1234,text/html,abc123...
```

### HTML
Interactive HTML report with syntax highlighting and statistics.

### SQLite
Database with searchable results:
```sql
SELECT * FROM scraped_data WHERE status = 200;
```

## Programmatic Usage

```python
import asyncio
from scrap import WebScraper
from config import Config

async def main():
    config = Config(
        max_requests=10,
        time_window=1.0,
        output_formats=['json', 'csv']
    )
    
    async with WebScraper(config=config, ctf_mode=False) as scraper:
        # Single URL
        result = await scraper.fetch('https://example.com')
        
        # Multiple URLs
        results = await scraper.fetch_multiple([
            'https://site1.com',
            'https://site2.com'
        ])
        
        # Crawl
        results = await scraper.crawl(
            start_url='https://example.com',
            max_depth=2
        )
        
        # Get stats
        stats = scraper.get_stats()
        print(stats)

asyncio.run(main())
```

## Architecture

### Components

1. **WebScraper**: Main scraper class coordinating all components
2. **RateLimiter**: Token bucket rate limiter with CTF mode
3. **ProxyManager**: Proxy rotation and health checking
4. **OutputHandler**: Multi-format output generation
5. **Config**: Configuration management

### Rate Limiting

Uses token bucket algorithm:
- Tokens refill at rate = max_requests / time_window
- Each request consumes 1 token
- CTF mode disables limiting (infinite tokens)

### Proxy Management

- Loads proxies from file
- Rotates through proxies
- Tracks success/failure rates
- Health checks proxies periodically
- Disables unhealthy proxies

## Use Cases

### CTF Competitions (Maximum Speed)
```bash
# Rust backend for maximum performance
python scraper.py --crawl https://ctf.example.com --language rust \
  --max-depth 15 --max-pages 50000 --max-connections 500 \
  --no-verify-ssl --fetch-resources

# Or Python with CTF mode
python cli.py --crawl https://ctf.example.com --ctf-mode --max-depth 5 --max-pages 1000
```

### Penetration Testing (Respectful)
```bash
# Python with rate limiting
python scraper.py --crawl https://target.com --language python \
  --max-requests 2 --time-window 1 --max-depth 3
```

### Data Collection
```bash
# Go for fast concurrent fetching
python scraper.py --url-file urls.txt --language go

# Python with multiple formats
python cli.py --url-file urls.txt --output json csv sqlite --save-files
```

### API Testing
```bash
# Python with custom headers
python scraper.py --url https://api.example.com/endpoint --language python \
  --header "Authorization: Bearer token"
```

## Security Considerations

- Always respect robots.txt
- Use appropriate rate limits for production systems
- Review scraped data for sensitive information
- Verify SSL certificates by default
- Don't scrape without permission

## Troubleshooting

### High Memory Usage
- Reduce `--max-connections`
- Use `--no-concurrent` for sequential processing
- Process results in batches

### Timeouts
- Increase `--timeout`
- Check network connectivity
- Verify proxy configuration

### Rate Limiting Issues
- Use `--ctf-mode` for CTFs
- Adjust `--max-requests` and `--time-window`
- Use proxy rotation

## License

MIT License

## Contributing

Contributions welcome! Please ensure code follows existing patterns and includes appropriate error handling.
