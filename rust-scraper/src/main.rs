use anyhow::{Context, Result};
use clap::Parser;
use dashmap::DashMap;
use indicatif::{ProgressBar, ProgressStyle};
use parking_lot::RwLock;
use scraper::{Html, Selector};
use reqwest::Client;
use serde::Serialize;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Semaphore;
use tracing::{info, warn, error};
use url::Url;
use chrono::Utc;
use console::Style;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Target URL to scrape
    #[arg(short, long)]
    url: Option<String>,

    /// File containing URLs (one per line)
    #[arg(long)]
    url_file: Option<String>,

    /// Crawl mode with max depth
    #[arg(long)]
    crawl: Option<String>,

    /// Maximum crawl depth
    #[arg(long, default_value_t = 10)]
    max_depth: usize,

    /// Maximum pages to crawl
    #[arg(long, default_value_t = 10000)]
    max_pages: usize,

    /// CTF mode (no rate limiting)
    #[arg(long)]
    ctf_mode: bool,

    /// Maximum concurrent requests
    #[arg(long, default_value_t = 500)]
    max_connections: usize,

    /// Request timeout in seconds
    #[arg(long, default_value_t = 30)]
    timeout: u64,

    /// Disable SSL verification
    #[arg(long)]
    no_verify_ssl: bool,

    /// Output directory
    #[arg(long, default_value = "data")]
    output_dir: String,

    /// Fetch resources (JS, CSS, images, etc.)
    #[arg(long, default_value_t = true)]
    fetch_resources: bool,

    /// User agent
    #[arg(long, default_value = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")]
    user_agent: String,

    /// Proxy URL
    #[arg(long)]
    proxy: Option<String>,

    /// Follow redirects
    #[arg(long, default_value_t = true)]
    follow_redirects: bool,

    /// Verbose output
    #[arg(long, short)]
    verbose: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum ResourceType {
    Js,
    Css,
    Image,
    Font,
    Html,
    Php,
    Json,
    Xml,
    Other,
}

impl ResourceType {
    fn from_url(url: &str, content_type: &str) -> Self {
        let url_lower = url.to_lowercase();
        let ct_lower = content_type.to_lowercase();

        if ct_lower.contains("javascript") || ct_lower.contains("js") || url_lower.ends_with(".js") {
            ResourceType::Js
        } else if ct_lower.contains("css") || url_lower.ends_with(".css") {
            ResourceType::Css
        } else if ct_lower.contains("image") || 
                 url_lower.ends_with(".png") || 
                 url_lower.ends_with(".jpg") || 
                 url_lower.ends_with(".jpeg") || 
                 url_lower.ends_with(".gif") || 
                 url_lower.ends_with(".svg") || 
                 url_lower.ends_with(".webp") || 
                 url_lower.ends_with(".ico") {
            ResourceType::Image
        } else if ct_lower.contains("font") || 
                 url_lower.ends_with(".woff") || 
                 url_lower.ends_with(".woff2") || 
                 url_lower.ends_with(".ttf") || 
                 url_lower.ends_with(".otf") || 
                 url_lower.ends_with(".eot") {
            ResourceType::Font
        } else if ct_lower.contains("html") || url_lower.ends_with(".html") || url_lower.ends_with(".htm") {
            ResourceType::Html
        } else if ct_lower.contains("php") || url_lower.ends_with(".php") {
            ResourceType::Php
        } else if ct_lower.contains("json") || url_lower.ends_with(".json") {
            ResourceType::Json
        } else if ct_lower.contains("xml") || url_lower.ends_with(".xml") {
            ResourceType::Xml
        } else {
            ResourceType::Other
        }
    }

    fn as_str(&self) -> &'static str {
        match self {
            ResourceType::Js => "js",
            ResourceType::Css => "css",
            ResourceType::Image => "images",
            ResourceType::Font => "fonts",
            ResourceType::Html => "html",
            ResourceType::Php => "php",
            ResourceType::Json => "json",
            ResourceType::Xml => "xml",
            ResourceType::Other => "other",
        }
    }
}

#[derive(Clone)]
struct TurboScraper {
    client: Client,
    args: Arc<Args>,
    visited: Arc<DashMap<String, bool>>,
    output_dir: PathBuf,
    stats: Arc<RwLock<ScraperStats>>,
    semaphore: Arc<Semaphore>,
}

#[derive(Debug, Default, Serialize)]
struct ScraperStats {
    total_requests: usize,
    successful: usize,
    failed: usize,
    bytes_downloaded: usize,
    start_time: Option<chrono::DateTime<chrono::Utc>>,
    end_time: Option<chrono::DateTime<chrono::Utc>>,
    resources_by_type: HashMap<String, usize>,
}

impl TurboScraper {
    fn new(args: Args) -> Result<Self> {
        let timeout = Duration::from_secs(args.timeout);
        
        let mut client_builder = Client::builder()
            .timeout(timeout)
            .user_agent(&args.user_agent)
            .pool_max_idle_per_host(100)
            .pool_idle_timeout(Duration::from_secs(90))
            .tcp_keepalive(Duration::from_secs(60))
            .connect_timeout(Duration::from_secs(10));

        if args.no_verify_ssl {
            client_builder = client_builder.danger_accept_invalid_certs(true);
        }

        if !args.follow_redirects {
            client_builder = client_builder.redirect(reqwest::redirect::Policy::none());
        }

        if let Some(proxy) = &args.proxy {
            client_builder = client_builder.proxy(reqwest::Proxy::all(proxy)?);
        }

        let client = client_builder.build()?;

        let output_dir = PathBuf::from(&args.output_dir);
        fs::create_dir_all(&output_dir)?;

        let semaphore = Arc::new(Semaphore::new(args.max_connections));

        Ok(Self {
            client,
            args: Arc::new(args),
            visited: Arc::new(DashMap::new()),
            output_dir,
            stats: Arc::new(RwLock::new(ScraperStats::default())),
            semaphore,
        })
    }

    fn get_site_name(&self, url: &str) -> Result<String> {
        let parsed = Url::parse(url)?;
        let domain = parsed.host_str().context("Invalid host")?;
        Ok(domain.replace('.', "_"))
    }

    fn get_file_path(&self, url: &str, resource_type: ResourceType, content_type: &str) -> Result<PathBuf> {
        let site_name = self.get_site_name(url)?;
        let type_dir = self.output_dir.join(&site_name).join(resource_type.as_str());
        fs::create_dir_all(&type_dir)?;

        let parsed = Url::parse(url)?;
        let path = parsed.path();
        
        let filename = if path.is_empty() || path == "/" {
            format!("index{}", self.get_extension(content_type))
        } else {
            let clean_path = path.trim_start_matches('/')
                .replace('/', "_")
                .replace('\\', "_");
            let without_query: String = clean_path.split('?').next().unwrap_or(&clean_path).to_string();
            
            if without_query.is_empty() {
                format!("index{}", self.get_extension(content_type))
            } else {
                let ext = if without_query.contains('.') {
                    String::new()
                } else {
                    self.get_extension(content_type)
                };
                format!("{}{}", without_query, ext)
            }
        };

        let filename = if filename.len() > 200 {
            format!("{}{}", &filename[..180], self.get_extension(content_type))
        } else {
            filename
        };

        Ok(type_dir.join(filename))
    }

    fn get_extension(&self, content_type: &str) -> String {
        let ct_lower = content_type.to_lowercase();
        
        if ct_lower.contains("html") {
            ".html".to_string()
        } else if ct_lower.contains("json") {
            ".json".to_string()
        } else if ct_lower.contains("css") {
            ".css".to_string()
        } else if ct_lower.contains("javascript") || ct_lower.contains("js") {
            ".js".to_string()
        } else if ct_lower.contains("jpeg") || ct_lower.contains("jpg") {
            ".jpg".to_string()
        } else if ct_lower.contains("png") {
            ".png".to_string()
        } else if ct_lower.contains("gif") {
            ".gif".to_string()
        } else if ct_lower.contains("svg") {
            ".svg".to_string()
        } else if ct_lower.contains("woff") {
            ".woff".to_string()
        } else if ct_lower.contains("ttf") {
            ".ttf".to_string()
        } else if ct_lower.contains("php") {
            ".php".to_string()
        } else if ct_lower.contains("xml") {
            ".xml".to_string()
        } else {
            ".txt".to_string()
        }
    }

    async fn fetch_url(&self, url: String, pb: Option<&ProgressBar>) -> Result<()> {
        let _permit = self.semaphore.acquire().await?;
        
        let response = self.client
            .get(&url)
            .send()
            .await
            .context("Failed to send request")?;

        let status = response.status();
        let content_type = response
            .headers()
            .get("content-type")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("text/plain")
            .to_string();

        let resource_type = ResourceType::from_url(&url, &content_type);

        if status.is_success() {
            let bytes = response.bytes().await?;
            let size = bytes.len();
            
            let file_path = self.get_file_path(&url, resource_type.clone(), &content_type)?;
            
            if resource_type == ResourceType::Image || resource_type == ResourceType::Font {
                fs::write(&file_path, bytes)?;
            } else {
                let text = String::from_utf8_lossy(&bytes).to_string();
                fs::write(&file_path, text)?;
            }

            {
                let mut stats = self.stats.write();
                stats.total_requests += 1;
                stats.successful += 1;
                stats.bytes_downloaded += size;
                *stats.resources_by_type.entry(resource_type.as_str().to_string()).or_insert(0) += 1;
            }

            if let Some(pb) = pb {
                pb.inc(1);
            }
        } else {
            let mut stats = self.stats.write();
            stats.total_requests += 1;
            stats.failed += 1;
            warn!("Failed to fetch {}: {}", url, status);
            
            if let Some(pb) = pb {
                pb.inc(1);
            }
        }

        Ok(())
    }

    fn extract_resources(&self, html: &str, base_url: &str) -> Vec<(String, ResourceType)> {
        let document = Html::parse_document(html);
        let mut resources = Vec::new();

        let script_selector = Selector::parse("script[src]").unwrap();
        for element in document.select(&script_selector) {
            if let Some(src) = element.value().attr("src") {
                if let Ok(full_url) = Url::parse(base_url).and_then(|base| base.join(src)) {
                    resources.push((full_url.to_string(), ResourceType::Js));
                }
            }
        }

        let link_selector = Selector::parse("link[rel='stylesheet']").unwrap();
        for element in document.select(&link_selector) {
            if let Some(href) = element.value().attr("href") {
                if let Ok(full_url) = Url::parse(base_url).and_then(|base| base.join(href)) {
                    resources.push((full_url.to_string(), ResourceType::Css));
                }
            }
        }

        let img_selector = Selector::parse("img[src]").unwrap();
        for element in document.select(&img_selector) {
            if let Some(src) = element.value().attr("src") {
                if let Ok(full_url) = Url::parse(base_url).and_then(|base| base.join(src)) {
                    resources.push((full_url.to_string(), ResourceType::Image));
                }
            }
        }

        let a_selector = Selector::parse("a[href]").unwrap();
        for element in document.select(&a_selector) {
            if let Some(href) = element.value().attr("href") {
                if let Ok(full_url) = Url::parse(base_url).and_then(|base| base.join(href)) {
                    resources.push((full_url.to_string(), ResourceType::Html));
                }
            }
        }

        resources
    }

    async fn crawl(&self, start_url: String) -> Result<()> {
        let base_url = Url::parse(&start_url)?;
        let base_domain = base_url.host_str().context("Invalid host")?.to_string();

        let mut to_visit: Vec<(String, usize)> = vec![(start_url, 0)];
        let mut resources_to_fetch: Vec<String> = Vec::new();
        let mut visited_count = 0;

        let pb = ProgressBar::new(self.args.max_pages as u64);
        pb.set_style(
            ProgressStyle::default_bar()
                .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} {msg}")
                .unwrap()
                .progress_chars("#>-"),
        );
        pb.set_message("Crawling...");

        while !to_visit.is_empty() && visited_count < self.args.max_pages {
            let (url, depth) = to_visit.pop().unwrap();

            if self.visited.contains_key(&url) {
                continue;
            }

            if depth > self.args.max_depth {
                continue;
            }

            if let Ok(parsed) = Url::parse(&url) {
                if let Some(host) = parsed.host_str() {
                    if host != base_domain {
                        continue;
                    }
                }
            }

            self.visited.insert(url.clone(), true);

            match self.fetch_url(url.clone(), Some(&pb)).await {
                Ok(_) => {
                    if self.args.fetch_resources {
                        let file_path = self.get_file_path(&url, ResourceType::Html, "text/html")?;
                        if let Ok(html_content) = fs::read_to_string(&file_path) {
                            let extracted = self.extract_resources(&html_content, &url);
                            for (res_url, _res_type) in extracted {
                                if !self.visited.contains_key(&res_url) {
                                    if depth < self.args.max_depth {
                                        to_visit.push((res_url.clone(), depth + 1));
                                    } else {
                                        resources_to_fetch.push(res_url);
                                    }
                                }
                            }
                        }
                    }
                    visited_count += 1;
                }
                Err(e) => {
                    error!("Error fetching {}: {}", url, e);
                }
            }
        }

        let resources_count = resources_to_fetch.len();
        if !resources_to_fetch.is_empty() {
            pb.set_length((resources_count + visited_count) as u64);
            pb.set_message("Fetching resources...");

            let scraper = self.clone();
            let fetch_tasks: Vec<_> = resources_to_fetch
                .into_iter()
                .map(|url| {
                    let scraper = scraper.clone();
                    async move {
                        scraper.fetch_url(url, None).await
                    }
                })
                .collect();

            let _ = futures::future::join_all(fetch_tasks).await;
            
            for _ in 0..resources_count {
                pb.inc(1);
            }
        }

        pb.finish_with_message("Scraping complete!");

        Ok(())
    }

    async fn run(&self) -> Result<()> {
        self.stats.write().start_time = Some(Utc::now());

        if let Some(crawl_url) = &self.args.crawl {
            info!("Starting crawl: {}", crawl_url);
            self.crawl(crawl_url.clone()).await?;
        } else if let Some(url) = &self.args.url {
            info!("Fetching: {}", url);
            let pb = ProgressBar::new(1);
            pb.set_style(ProgressStyle::default_bar().template("{spinner:.green} {msg}").unwrap());
            pb.set_message("Fetching...");
            
            self.fetch_url(url.clone(), Some(&pb)).await?;
            pb.finish_with_message("Done!");
        } else if let Some(url_file) = &self.args.url_file {
            let urls = fs::read_to_string(url_file)?
                .lines()
                .filter(|line| !line.trim().is_empty() && !line.trim().starts_with('#'))
                .map(|line| line.trim().to_string())
                .collect::<Vec<_>>();

            info!("Fetching {} URLs from file", urls.len());

            let pb = ProgressBar::new(urls.len() as u64);
            pb.set_style(
                ProgressStyle::default_bar()
                    .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} {msg}")
                    .unwrap()
                    .progress_chars("#>-"),
            );
            pb.set_message("Fetching URLs...");

            let scraper = self.clone();
            let fetch_tasks: Vec<_> = urls
                .into_iter()
                .map(|url| {
                    let scraper = scraper.clone();
                    let pb = pb.clone();
                    async move {
                        scraper.fetch_url(url, Some(&pb)).await
                    }
                })
                .collect();

            let _ = futures::future::join_all(fetch_tasks).await;
            pb.finish_with_message("Done!");
        }

        self.stats.write().end_time = Some(Utc::now());
        self.print_stats();

        Ok(())
    }

    fn print_stats(&self) {
        let stats = self.stats.read();
        let green = Style::new().green();
        let cyan = Style::new().cyan();
        let yellow = Style::new().yellow();

        println!("\n{}", green.apply_to("═".repeat(50)));
        println!("{}", green.apply_to("Scraping Statistics"));
        println!("{}", green.apply_to("═".repeat(50)));
        println!("{}: {}", cyan.apply_to("Total requests"), stats.total_requests);
        println!("{}: {}", cyan.apply_to("Successful"), green.apply_to(stats.successful));
        println!("{}: {}", cyan.apply_to("Failed"), yellow.apply_to(stats.failed));
        println!("{}: {}", cyan.apply_to("Bytes downloaded"), stats.bytes_downloaded);
        
        if let (Some(start), Some(end)) = (stats.start_time, stats.end_time) {
            let duration = end.signed_duration_since(start);
            println!("{}: {}", cyan.apply_to("Duration"), format!("{} seconds", duration.num_seconds()));
            
            if duration.num_seconds() > 0 {
                let speed = stats.bytes_downloaded as f64 / duration.num_seconds() as f64 / 1024.0;
                println!("{}: {:.2} KB/s", cyan.apply_to("Average speed"), speed);
            }
        }

        println!("\n{}", cyan.apply_to("Resources by type:"));
        for (rtype, count) in &stats.resources_by_type {
            println!("  {}: {}", cyan.apply_to(rtype), count);
        }
        println!("{}", green.apply_to("═".repeat(50)));
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    let log_level = if args.verbose { "debug" } else { "info" };
    tracing_subscriber::fmt()
        .with_env_filter(format!("turbo_scraper={}", log_level))
        .init();

    let green = Style::new().green();
    println!("{}", green.apply_to("🚀 Turbo Scraper - Ultra High Performance Web Scraper"));
    println!();

    let scraper = TurboScraper::new(args)?;
    scraper.run().await?;

    Ok(())
}
