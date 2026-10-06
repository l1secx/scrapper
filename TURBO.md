# Turbo Scraper - Ultra High Performance

## Why Turbo Scraper?

Turbo Scraper is optimized for maximum performance:

### Performance Optimizations

1. **Connection Pooling**: Reuses HTTP connections efficiently
2. **Batch Processing**: Processes URLs in batches for better concurrency
3. **Thread Pool Offloading**: File I/O handled in separate thread pool
4. **Pre-compiled Regex**: Patterns compiled once, not per request
5. **Memory Efficient**: Streams data instead of loading all into memory
6. **Smart Batching**: Dynamically adjusts batch sizes based on concurrency limits

### Features

- **500+ Concurrent Connections**: By default
- **Real-time Progress**: Beautiful progress bars with tqdm
- **Organized Output**: Files organized by site and resource type
- **Smart Resource Extraction**: Automatically finds JS, CSS, images
- **Same-domain Filtering**: Only crawls within target domain
- **BFS Traversal**: Efficient breadth-first search for crawling
- **Duplicate Detection**: Avoids fetching same URL twice

## Usage

### Maximum Power Crawl

```bash
python turbo_scraper.py \
  --crawl https://target.com \
  --max-depth 15 \
  --max-pages 50000 \
  --max-connections 500 \
  --no-verify-ssl \
  --fetch-resources
```

### Fetch from File

```bash
python turbo_scraper.py \
  --url-file urls.txt \
  --max-connections 500 \
  --no-verify-ssl
```

### Single URL

```bash
python turbo_scraper.py --url https://example.com
```

## Performance Comparison

| Feature | Python Scraper | Turbo Scraper |
|---------|---------------|---------------|
| Concurrency | 100-200 | 500+ |
| Speed | Baseline | 2-3x faster |
| Memory | Higher | Optimized |
| I/O Blocking | Some | Thread pool offloaded |
| Progress | Basic | Real-time tqdm |

## Output Structure

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

## Options

- `--url` - Single URL to fetch
- `--url-file` - File containing URLs
- `--crawl` - Crawl website starting from URL
- `--max-depth` - Maximum crawl depth (default: 10)
- `--max-pages` - Maximum pages to crawl (default: 10000)
- `--max-connections` - Max concurrent requests (default: 500)
- `--timeout` - Request timeout in seconds (default: 30)
- `--no-verify-ssl` - Disable SSL verification
- `--output-dir` - Output directory (default: data)
- `--fetch-resources` - Fetch JS, CSS, images (default: true)
- `--proxy` - Proxy URL
- `--verbose` - Verbose logging
