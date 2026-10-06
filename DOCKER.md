# Docker Setup Guide

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and run
docker-compose up -d

# Access web GUI
# Open http://localhost:5000 in your browser
```

### Using Docker directly

```bash
# Build image
docker build -t multi-language-scraper .

# Run container
docker run -d -p 5000:5000 -v $(pwd)/data:/app/data multi-language-scraper

# Access web GUI
# Open http://localhost:5000 in your browser
```

## Features

- **Web GUI**: Beautiful web interface for scraping
- **Multi-Language**: Choose Python, Rust, Go, or Collaborative mode
- **Real-time Progress**: Monitor scraping progress in real-time
- **File Download**: Download scraped files directly from web
- **Batch Download**: Download all files as ZIP
- **Task Management**: View and manage scraping tasks
- **Statistics**: View scraping statistics

## Web Interface

### Main Features

1. **Scraping Form**
   - Enter URL to scrape
   - Select language (Python, Rust, Go, Collaborative)
   - Configure options (CTF mode, files only, fetch resources)
   - Set max depth and max pages

2. **Real-time Progress**
   - Progress bar showing scraping status
   - Task status updates
   - Log output

3. **File Management**
   - List all downloaded files
   - Download individual files
   - Download all files as ZIP
   - Clear all files

4. **Statistics**
   - Total files downloaded
   - Total size
   - Active tasks
   - Completed tasks

## API Endpoints

### Scraping
- `POST /api/scrape` - Start a new scrape task
- `GET /api/tasks/<task_id>` - Get task status
- `GET /api/tasks` - List all tasks

### Files
- `GET /api/files` - List downloaded files
- `GET /api/download/<filename>` - Download a file
- `GET /api/download-all` - Download all files as ZIP
- `POST /api/clear-files` - Clear all files

### Stats
- `GET /api/stats` - Get system statistics

## Volume Mounting

Mount local directories to persist data:

```bash
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  multi-language-scraper
```

## Environment Variables

- `PYTHONUNBUFFERED=1` - Disable Python output buffering

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose build --no-cache
```

### Can't access web interface
```bash
# Check if port is in use
lsof -i :5000

# Use different port
docker run -d -p 8080:5000 multi-language-scraper
```

### Files not persisting
```bash
# Ensure volume is mounted
docker inspect <container_id>
```

## Building Without Docker

If you want to run the web app without Docker:

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r web/requirements.txt

# Build Rust and Go scrapers
cd rust-scraper && cargo build --release && cd ..
cd go-scraper && go build -o turbo-scraper && cd ..

# Run web app
python web/app.py
```

Then open http://localhost:5000 in your browser.
