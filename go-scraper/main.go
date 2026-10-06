package main

import (
	"crypto/tls"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
)

type simpleProgressBar struct {
	current int64
	total   int64
}

func (pb *simpleProgressBar) start(description string) {
	fmt.Printf("%s...\n", description)
}

func (pb *simpleProgressBar) Add(delta int) {
	pb.current += int64(delta)
	if pb.total > 0 {
		fmt.Printf("\rProgress: %d/%d", pb.current, pb.total)
	}
}

func (pb *simpleProgressBar) Finish() {
	fmt.Printf("\rProgress: %d/%d - Complete!\n", pb.current, pb.total)
}

type Config struct {
	MaxConnections int
	Timeout         int
	OutputDir       string
	VerifySSL       bool
	UserAgent       string
	Proxy           string
	FollowRedirects bool
}

type Resource struct {
	URL         string
	ContentType string
	Size        int64
	ResourceType string
}

type TurboScraper struct {
	config      Config
	client      *http.Client
	visited     map[string]bool
	visitedMutex sync.RWMutex
	stats       Stats
	statsMutex  sync.Mutex
	outputDir   string
}

type Stats struct {
	TotalRequests  int
	Successful     int
	Failed         int
	BytesDownloaded int64
	ResourcesByType map[string]int
}

func NewTurboScraper(config Config) *TurboScraper {
	transport := &http.Transport{
		MaxIdleConns:        100,
		IdleConnTimeout:     90 * time.Second,
		DisableCompression:  false,
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: !config.VerifySSL,
		},
	}

	client := &http.Client{
		Transport: transport,
		Timeout:   time.Duration(config.Timeout) * time.Second,
	}

	if config.Proxy != "" {
		proxyURL, _ := url.Parse(config.Proxy)
		transport.Proxy = http.ProxyURL(proxyURL)
	}

	return &TurboScraper{
		config:   config,
		client:   client,
		visited:  make(map[string]bool),
		stats: Stats{
			ResourcesByType: make(map[string]int),
		},
		outputDir: config.OutputDir,
	}
}

func (ts *TurboScraper) getSiteName(urlStr string) string {
	parsed, _ := url.Parse(urlStr)
	domain := parsed.Host
	domain = strings.Replace(domain, "www.", "", 1)
	return strings.Replace(domain, ".", "_", -1)
}

func (ts *TurboScraper) getResourceType(urlStr, contentType string) string {
	urlLower := strings.ToLower(urlStr)
	ctLower := strings.ToLower(contentType)

	if strings.Contains(ctLower, "javascript") || strings.Contains(ctLower, "js") || strings.HasSuffix(urlLower, ".js") {
		return "js"
	} else if strings.Contains(ctLower, "css") || strings.HasSuffix(urlLower, ".css") {
		return "css"
	} else if strings.Contains(ctLower, "image") || 
		strings.HasSuffix(urlLower, ".png") || 
		strings.HasSuffix(urlLower, ".jpg") || 
		strings.HasSuffix(urlLower, ".jpeg") || 
		strings.HasSuffix(urlLower, ".gif") || 
		strings.HasSuffix(urlLower, ".svg") || 
		strings.HasSuffix(urlLower, ".webp") || 
		strings.HasSuffix(urlLower, ".ico") {
		return "images"
	} else if strings.Contains(ctLower, "font") || 
		strings.HasSuffix(urlLower, ".woff") || 
		strings.HasSuffix(urlLower, ".woff2") || 
		strings.HasSuffix(urlLower, ".ttf") || 
		strings.HasSuffix(urlLower, ".otf") || 
		strings.HasSuffix(urlLower, ".eot") {
		return "fonts"
	} else if strings.Contains(ctLower, "html") || strings.HasSuffix(urlLower, ".html") || strings.HasSuffix(urlLower, ".htm") {
		return "html"
	} else if strings.Contains(ctLower, "php") || strings.HasSuffix(urlLower, ".php") {
		return "php"
	} else if strings.Contains(ctLower, "json") || strings.HasSuffix(urlLower, ".json") {
		return "json"
	} else if strings.Contains(ctLower, "xml") || strings.HasSuffix(urlLower, ".xml") {
		return "xml"
	}
	return "other"
}

func (ts *TurboScraper) getExtension(contentType string) string {
	ctLower := strings.ToLower(contentType)
	
	if strings.Contains(ctLower, "html") {
		return ".html"
	} else if strings.Contains(ctLower, "json") {
		return ".json"
	} else if strings.Contains(ctLower, "css") {
		return ".css"
	} else if strings.Contains(ctLower, "javascript") || strings.Contains(ctLower, "js") {
		return ".js"
	} else if strings.Contains(ctLower, "jpeg") || strings.Contains(ctLower, "jpg") {
		return ".jpg"
	} else if strings.Contains(ctLower, "png") {
		return ".png"
	} else if strings.Contains(ctLower, "gif") {
		return ".gif"
	} else if strings.Contains(ctLower, "svg") {
		return ".svg"
	} else if strings.Contains(ctLower, "woff") {
		return ".woff"
	} else if strings.Contains(ctLower, "ttf") {
		return ".ttf"
	} else if strings.Contains(ctLower, "php") {
		return ".php"
	} else if strings.Contains(ctLower, "xml") {
		return ".xml"
	}
	return ".txt"
}

func (ts *TurboScraper) getFilePath(urlStr, resourceType, contentType string) (string, error) {
	siteName := ts.getSiteName(urlStr)
	typeDir := filepath.Join(ts.outputDir, siteName, resourceType)
	
	if err := os.MkdirAll(typeDir, 0755); err != nil {
		return "", err
	}
	
	parsed, _ := url.Parse(urlStr)
	path := parsed.Path
	
	var filename string
	if path == "" || path == "/" {
		filename = "index" + ts.getExtension(contentType)
	} else {
		cleanPath := strings.TrimPrefix(path, "/")
		cleanPath = strings.ReplaceAll(cleanPath, "/", "_")
		cleanPath = strings.ReplaceAll(cleanPath, "\\", "_")
		
		parts := strings.Split(cleanPath, "?")
		cleanPath = parts[0]
		
		if cleanPath == "" {
			filename = "index" + ts.getExtension(contentType)
		} else {
			if !strings.Contains(cleanPath, ".") {
				filename = cleanPath + ts.getExtension(contentType)
			} else {
				filename = cleanPath
			}
		}
	}
	
	if len(filename) > 200 {
		filename = filename[:180] + ts.getExtension(contentType)
	}
	
	return filepath.Join(typeDir, filename), nil
}

func (ts *TurboScraper) fetchURL(urlStr string, pb *simpleProgressBar) error {
	ts.visitedMutex.Lock()
	if ts.visited[urlStr] {
		ts.visitedMutex.Unlock()
		return nil
	}
	ts.visited[urlStr] = true
	ts.visitedMutex.Unlock()

	req, _ := http.NewRequest("GET", urlStr, nil)
	req.Header.Set("User-Agent", ts.config.UserAgent)
	req.Header.Set("Accept", "*/*")
	req.Header.Set("Accept-Encoding", "gzip, deflate")
	req.Header.Set("Connection", "keep-alive")

	resp, err := ts.client.Do(req)
	if err != nil {
		ts.statsMutex.Lock()
		ts.stats.Failed++
		ts.stats.TotalRequests++
		ts.statsMutex.Unlock()
		return err
	}
	defer resp.Body.Close()

	contentType := resp.Header.Get("Content-Type")
	if contentType == "" {
		contentType = "text/plain"
	}

	resourceType := ts.getResourceType(urlStr, contentType)

	if resp.StatusCode == 200 {
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return err
		}

		filePath, err := ts.getFilePath(urlStr, resourceType, contentType)
		if err != nil {
			return err
		}

		if err := os.WriteFile(filePath, body, 0644); err != nil {
			return err
		}

		ts.statsMutex.Lock()
		ts.stats.Successful++
		ts.stats.TotalRequests++
		ts.stats.BytesDownloaded += int64(len(body))
		ts.stats.ResourcesByType[resourceType]++
		ts.statsMutex.Unlock()
	} else {
		ts.statsMutex.Lock()
		ts.stats.Failed++
		ts.stats.TotalRequests++
		ts.statsMutex.Unlock()
	}

	if pb != nil {
		pb.Add(1)
	}
	return nil
}

func (ts *TurboScraper) extractResources(htmlContent, baseURL string) []string {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(htmlContent))
	if err != nil {
		return nil
	}

	var resources []string

	doc.Find("script[src]").Each(func(i int, s *goquery.Selection) {
		if src, exists := s.Attr("src"); exists {
			resolvedURL, _ := url.Parse(baseURL)
			resolvedURL.Path = src
			resources = append(resources, resolvedURL.String())
		}
	})

	doc.Find("link[rel='stylesheet']").Each(func(i int, s *goquery.Selection) {
		if href, exists := s.Attr("href"); exists {
			resolvedURL, _ := url.Parse(baseURL)
			resolvedURL.Path = href
			resources = append(resources, resolvedURL.String())
		}
	})

	doc.Find("img[src]").Each(func(i int, s *goquery.Selection) {
		if src, exists := s.Attr("src"); exists {
			resolvedURL, _ := url.Parse(baseURL)
			resolvedURL.Path = src
			resources = append(resources, resolvedURL.String())
		}
	})

	doc.Find("a[href]").Each(func(i int, s *goquery.Selection) {
		if href, exists := s.Attr("href"); exists {
			resolvedURL, _ := url.Parse(baseURL)
			resolvedURL.Path = href
			resources = append(resources, resolvedURL.String())
		}
	})

	return resources
}

func (ts *TurboScraper) crawl(startURL string, maxDepth, maxPages int, fetchResources bool) error {
	baseURL, _ := url.Parse(startURL)
	baseDomain := baseURL.Host

	var toVisit []struct {
		url   string
		depth int
	}
	toVisit = append(toVisit, struct{ url string; depth int }{startURL, 0})

	var resourcesToFetch []string
	visitedCount := 0

	pb := simpleProgressBar{
		total: int64(maxPages),
	}
	
	pb.start("Crawling")

	for len(toVisit) > 0 && visitedCount < maxPages {
		item := toVisit[0]
		toVisit = toVisit[1:]

		if item.depth > maxDepth {
			continue
		}

		parsed, _ := url.Parse(item.url)
		if parsed.Host != baseDomain {
			continue
		}

		if err := ts.fetchURL(item.url, &pb); err == nil {
			visitedCount++

			if fetchResources {
				filePath, _ := ts.getFilePath(item.url, "html", "text/html")
				if htmlContent, err := os.ReadFile(filePath); err == nil {
					resources := ts.extractResources(string(htmlContent), item.url)
					for _, resURL := range resources {
						ts.visitedMutex.RLock()
						visited := ts.visited[resURL]
						ts.visitedMutex.RUnlock()

						if !visited {
							resParsed, _ := url.Parse(resURL)
							if resParsed.Host == baseDomain {
								if item.depth < maxDepth {
									toVisit = append(toVisit, struct{ url string; depth int }{resURL, item.depth + 1})
								} else {
									resourcesToFetch = append(resourcesToFetch, resURL)
								}
							}
						}
					}
				}
			}
		}
	}

	if len(resourcesToFetch) > 0 {
		pb.total = int64(len(resourcesToFetch) + visitedCount)
		pb.start("Fetching resources")

		sem := make(chan struct{}, ts.config.MaxConnections)
		var wg sync.WaitGroup

		for _, resURL := range resourcesToFetch {
			wg.Add(1)
			go func(url string) {
				defer wg.Done()
				sem <- struct{}{}
				ts.fetchURL(url, &pb)
				<-sem
			}(resURL)
		}

		wg.Wait()
	}

	pb.Finish()
	return nil
}

func (ts *TurboScraper) fetchMultiple(urls []string) error {
	pb := simpleProgressBar{
		total: int64(len(urls)),
	}
	pb.start("Fetching")

	sem := make(chan struct{}, ts.config.MaxConnections)
	var wg sync.WaitGroup

	for _, urlStr := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			sem <- struct{}{}
			ts.fetchURL(u, &pb)
			<-sem
		}(urlStr)
	}

	wg.Wait()
	pb.Finish()
	return nil
}

func (ts *TurboScraper) printStats() {
	fmt.Println("\n" + strings.Repeat("=", 50))
	fmt.Println("Scraping Statistics")
	fmt.Println(strings.Repeat("=", 50))
	fmt.Printf("Total requests: %d\n", ts.stats.TotalRequests)
	fmt.Printf("Successful: %d\n", ts.stats.Successful)
	fmt.Printf("Failed: %d\n", ts.stats.Failed)
	fmt.Printf("Bytes downloaded: %d\n", ts.stats.BytesDownloaded)
	fmt.Println("\nResources by type:")
	for rtype, count := range ts.stats.ResourcesByType {
		fmt.Printf("  %s: %d\n", rtype, count)
	}
	fmt.Println(strings.Repeat("=", 50))
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: turbo-scraper <url>")
		os.Exit(1)
	}

	config := Config{
		MaxConnections: 500,
		Timeout:         30,
		OutputDir:       "data",
		VerifySSL:       true,
		UserAgent:       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
		FollowRedirects: true,
	}

	scraper := NewTurboScraper(config)

	startURL := os.Args[1]
	fmt.Println("🚀 Turbo Scraper (Go) - Ultra High Performance")
	fmt.Println()

	if err := scraper.crawl(startURL, 10, 10000, true); err != nil {
		fmt.Printf("Error: %v\n", err)
	}

	scraper.printStats()
}
