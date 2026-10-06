"""
Configuration Module
Handles scraper configuration
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class Config:
    """Configuration for web scraper"""
    
    # Rate limiting
    max_requests: int = 10
    time_window: float = 1.0  # seconds
    
    # Connection settings
    max_connections: int = 100
    timeout: int = 30
    verify_ssl: bool = True
    follow_redirects: bool = True
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    
    # Proxy settings
    proxy_file: Optional[str] = None
    rotate_proxies: bool = False
    
    # Output settings
    output_formats: List[str] = field(default_factory=lambda: ['json'])
    
    # Custom headers
    custom_headers: Optional[Dict[str, str]] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'Config':
        """Create Config from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> Dict:
        """Convert Config to dictionary"""
        return {
            'max_requests': self.max_requests,
            'time_window': self.time_window,
            'max_connections': self.max_connections,
            'timeout': self.timeout,
            'verify_ssl': self.verify_ssl,
            'follow_redirects': self.follow_redirects,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'proxy_file': self.proxy_file,
            'rotate_proxies': self.rotate_proxies,
            'output_formats': self.output_formats,
            'custom_headers': self.custom_headers
        }
