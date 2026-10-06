# Unified Scraper - Multi-language Web Scraper

Professional web scraper with support for **Python**, **Rust**, and **Go** backends. Choose the best language for your needs!

## 🚀 Quick Start

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

# Run scraper (auto-selects best available language)
python scraper.py --crawl https://example.com

# Or specify language explicitly
python scraper.py --crawl https://example.com --language rust
python scraper.py --crawl https://example.com --language go
python scraper.py --crawl https://example.com --language python
```

## 📊 Language Comparison

| Feature | Python | Rust | Go |
|---------|--------|------|-----|
| **Speed** | Baseline | 10-100x faster | 5-50x faster |
| **Features** | Most features | High performance | Fast & concurrent |
| **Ease of Use** | Easiest | Requires build | Requires build |
| **Memory** | Higher | Very efficient | Efficient |
| **Concurrency** | Async/await | True multi-threaded | Goroutines |
| **Rate Limiting** | ✅ Full support | ❌ CTF mode only | ❌ CTF mode only |
| **Proxy** | ✅ Rotation | ✅ Basic | ❌ None |
| **Use Case** | Production/CTF | Maximum speed | Fast deployment |

## 🎯 Choose Your Language

### Python - Feature-Rich Production Scraper
Best for: Production use, rate limiting, proxy rotation, extensive features

```bash
python scraper.py --crawl https://target.com --language python \
  --max-requests 5 --time-window 2 \
  --proxy-file proxies.txt --rotate-proxies \
  --output json csv html sqlite
```

**Features:**
- Rate limiting with token bucket algorithm
- Proxy rotation with health checking
- Multiple output formats (JSON, CSV, HTML, SQLite)
- Custom headers and retry logic
- Resource extraction (JS, CSS, images, fonts)
- Organized file output by site and type

### Rust - Maximum Performance
Best for: CTF competitions, bulk scraping, maximum speed

```bash
python scraper.py --crawl https://target.com --language rust \
  --max-depth 15 --max-pages 50000 \
  --max-connections 500 --no-verify-ssl \
  --fetch-resources
```

**Features:**
- Native compiled performance (10-100x faster than Python)
- True multi-threaded parallelism with Tokio
- 500+ concurrent connections
- Zero-cost abstractions
- Memory efficient
- Connection pooling
- Real-time progress bars

### Go - Fast & Concurrent
Best for: Fast deployment, concurrent operations, balance of speed and features

```bash
python scraper.py --crawl https://target.com --language go
```

**Features:**
- Fast concurrent execution with goroutines
- Easy deployment (single binary)
- Efficient memory usage
- HTML parsing with goquery
- Progress bars
- Organized file output

## 📁 Project Structure

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

## 🎮 Usage Examples

### CTF Competition (Maximum Speed)
```bash
# Rust for maximum performance
python scraper.py --crawl https://ctf.target.com --language rust \
  --max-depth 15 --max-pages 50000 --max-connections 500 \
  --no-verify-ssl --fetch-resources
```

### Pentest (Respectful Scraping)
```bash
# Python with rate limiting
python scraper.py --crawl https://target.com --language python \
  --max-requests 2 --time-window 1 --max-depth 3 \
  --output json csv
```

### Bulk Data Collection
```bash
# Go for fast concurrent fetching
python scraper.py --url-file urls.txt --language go
```

### API Testing
```bash
# Python with custom headers
python scraper.py --url https://api.example.com/endpoint \
  --language python --header "Authorization: Bearer token"
```

## 🔧 Command Line Options

### Input
- `--url, -u` - Single URL
- `--url-file` - File with URLs
- `--crawl` - Crawl website

### Crawl
- `--max-depth` - Maximum depth (default: 10)
- `--max-pages` - Maximum pages (default: 10000)
- `--follow-pattern` - Regex pattern to follow
- `--exclude-pattern` - Regex pattern to exclude

### Rate Limiting (Python only)
- `--ctf-mode` - Disable rate limiting
- `--max-requests` - Requests per time window
- `--time-window` - Time window in seconds

### Connection
- `--max-connections` - Max concurrent (default: 500)
- `--timeout` - Request timeout (default: 30)
- `--no-verify-ssl` - Disable SSL
- `--no-redirects` - No redirects

### Output
- `--output, -o` - Format: json, csv, html, sqlite
- `--output-dir` - Output directory
- `--data-dir` - Data directory
- `--save-files` - Save files
- `--files-only` - Only files, no metadata
- `--fetch-resources` - Fetch JS, CSS, images

### Language
- `--language, -l` - python, rust, go, auto
- `--no-prompt` - Skip language selection

### Other
- `--verbose, -v` - Verbose output

## 📦 Installation

### Python
```bash
pip install -r requirements.txt
```

### Rust (Optional)
```bash
cd rust-scraper
cargo build --release
```

### Go (Optional)
```bash
cd go-scraper
go mod download
go build -o turbo-scraper
```

## 🎯 When to Use Which Language?

| Scenario | Recommended Language | Reason |
|----------|---------------------|--------|
| CTF Competition | Rust | Maximum speed, no rate limiting |
| Production Pentest | Python | Rate limiting, proxy rotation |
| Bulk Downloading | Rust/Go | High throughput |
| API Testing | Python | Custom headers, retry logic |
| Quick Testing | Python | No build required |
| Deployment | Go | Single binary, easy deployment |
| Maximum Speed | Rust | Native compiled |

## 💡 Tips

1. **Use Rust** for CTF and bulk scraping where speed is critical
2. **Use Python** for production where rate limiting and features matter
3. **Use Go** for balance of speed and easy deployment
4. **Use auto** to let the script choose the best available
5. Build Rust and Go once, then use them for all future scrapes

## 📊 Output Structure

All languages organize output by site and resource type:

```
data/
└── example_com/
    ├── js/
    ├── css/
    ├── images/
    ├── fonts/
    ├── html/
    └── php/
```

## 🔗 Links

- [Python Scraper Documentation](README.md)
- [Turbo Python Documentation](TURBO.md)
- [Rust Scraper Documentation](rust-scraper/README.md)
