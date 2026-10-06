.PHONY: all build clean python rust go test help

all: build

build: python rust go

python:
	@echo "Python dependencies..."
	pip install -r requirements.txt

rust:
	@echo "Building Rust scraper..."
	cd rust-scraper && cargo build --release

go:
	@echo "Building Go scraper..."
	cd go-scraper && go build -o turbo-scraper

clean:
	@echo "Cleaning build artifacts..."
	rm -rf rust-scraper/target
	rm -f go-scraper/turbo-scraper
	rm -rf data output

test:
	@echo "Testing unified scraper..."
	python scraper.py --help

help:
	@echo "Available targets:"
	@echo "  all    - Build all scrapers"
	@echo "  python - Install Python dependencies"
	@echo "  rust   - Build Rust scraper"
	@echo "  go     - Build Go scraper"
	@echo "  clean  - Remove build artifacts"
	@echo "  test   - Test unified scraper"
	@echo "  help   - Show this help"
