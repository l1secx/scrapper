# Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### 1. Simple Scraping

```bash
# Scrape a single URL
python cli.py --url https://example.com

# Output will be saved to output/results_YYYYMMDD_HHMMSS.json
```

### 2. CTF Mode (No Rate Limiting)

```bash
# Maximum speed for CTF competitions
python cli.py --url https://ctf.example.com --ctf-mode
```

### 3. Multiple URLs

```bash
# Scrape multiple URLs
python cli.py --urls https://site1.com https://site2.com https://site3.com

# Or read from file
python cli.py --url-file urls.txt
```

### 4. Web Crawling

```bash
# Crawl website with depth 2
python cli.py --crawl https://example.com --max-depth 2

# Crawl with patterns
python cli.py --crawl https://example.com --follow-pattern "/api/" --max-depth 3
```

### 5. Multiple Output Formats

```bash
# Save in multiple formats
python cli.py --url https://example.com --output json csv html sqlite

# Save content to files
python cli.py --url https://example.com --save-files
```

### 6. Rate Limiting

```bash
# Custom rate limit (5 requests per 2 seconds)
python cli.py --url https://example.com --max-requests 5 --time-window 2

# Check available tokens info in logs
```

### 7. Proxy Support

```bash
# Use proxies from file
python cli.py --url https://example.com --proxy-file proxies.txt

# Rotate through proxies
python cli.py --url https://example.com --proxy-file proxies.txt --rotate-proxies
```

### 8. Custom Headers

```bash
# Add custom header
python cli.py --url https://example.com --header "Authorization: Bearer token"

# Multiple headers
python cli.py --url https://example.com --header "Authorization: Bearer token" --header "X-API-Key: abc123"
```

## Common Use Cases

### CTF Competition
```bash
# Fast, unlimited scraping
python cli.py --crawl https://ctf.target.com --ctf-mode --max-depth 5 --max-pages 1000 --output json
```

### Pentest (Respectful)
```bash
# Rate-limited, careful scraping
python cli.py --crawl https://target.com --max-requests 2 --time-window 1 --max-depth 3 --output json csv
```

### Data Collection
```bash
# Collect data with multiple formats
python cli.py --url-file urls.txt --output json csv sqlite --save-files --verbose
```

### API Testing
```bash
# Test API endpoints
python cli.py --url https://api.example.com/endpoint --header "Authorization: Bearer token" --output json
```

## Output Files

- `output/results_*.json` - JSON output
- `output/results_*.csv` - CSV output
- `output/results_*.html` - HTML report
- `output/results_*.db` - SQLite database
- `output/scraper.log` - Log file
- `output/stats.json` - Statistics
- `data/*.html` - Downloaded content (if --save-files)

## Getting Help

```bash
# Show all options
python cli.py --help

# Show specific section help
python cli.py --help | grep -A 10 "Rate Limiting"
```

## Examples

See `example_usage.py` for programmatic usage examples.
