"""
Proxy Manager Module
Handles proxy rotation and health checking
"""

import asyncio
import aiohttp
from typing import Optional, List, Dict
from pathlib import Path
import logging
from dataclasses import dataclass, field


@dataclass
class Proxy:
    """Proxy data class"""
    url: str
    protocol: str = 'http'
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0
    is_healthy: bool = True
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total


@dataclass
class ProxyManager:
    """
    Proxy manager with rotation and health checking
    """
    
    proxy_file: Optional[str] = None
    rotate_proxies: bool = False
    health_check_interval: int = 300  # seconds
    min_success_rate: float = 0.5
    
    def __post_init__(self):
        self.proxies: List[Proxy] = []
        self.current_index = 0
        self.logger = logging.getLogger('ProxyManager')
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def load_proxies(self):
        """Load proxies from file"""
        if not self.proxy_file:
            self.logger.info("No proxy file specified, running without proxies")
            return
        
        proxy_path = Path(self.proxy_file)
        if not proxy_path.exists():
            self.logger.warning(f"Proxy file not found: {self.proxy_file}")
            return
        
        with open(proxy_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxy = Proxy(url=line)
                    self.proxies.append(proxy)
        
        self.logger.info(f"Loaded {len(self.proxies)} proxies from {self.proxy_file}")
        
        # Start health check task if proxies are loaded
        if self.proxies and self.rotate_proxies:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def get_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.proxies:
            return None
        
        if not self.rotate_proxies:
            # Return first healthy proxy
            for proxy in self.proxies:
                if proxy.is_healthy:
                    return proxy.url
            return None
        
        # Rotate through proxies
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if proxy.is_healthy:
                proxy.last_used = asyncio.get_event_loop().time()
                return proxy.url
            
            attempts += 1
        
        self.logger.warning("No healthy proxies available")
        return None
    
    async def report_success(self, proxy_url: str):
        """Report successful proxy usage"""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.success_count += 1
                proxy.is_healthy = True
                break
    
    async def report_failure(self, proxy_url: str):
        """Report failed proxy usage"""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.failure_count += 1
                
                # Mark as unhealthy if success rate drops below threshold
                if proxy.success_rate < self.min_success_rate:
                    proxy.is_healthy = False
                    self.logger.warning(f"Proxy {proxy_url} marked as unhealthy (success rate: {proxy.success_rate:.2f})")
                break
    
    async def _health_check_loop(self):
        """Periodically check proxy health"""
        while True:
            await asyncio.sleep(self.health_check_interval)
            await self._check_proxy_health()
    
    async def _check_proxy_health(self):
        """Check health of all proxies"""
        self.logger.info("Running proxy health check...")
        
        async with aiohttp.ClientSession() as session:
            tasks = [self._check_single_proxy(session, proxy) for proxy in self.proxies]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = sum(1 for p in self.proxies if p.is_healthy)
        self.logger.info(f"Health check complete: {healthy_count}/{len(self.proxies)} proxies healthy")
    
    async def _check_single_proxy(self, session: aiohttp.ClientSession, proxy: Proxy):
        """Check health of a single proxy"""
        try:
            async with session.get(
                'http://httpbin.org/ip',
                proxy=proxy.url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    proxy.is_healthy = True
                else:
                    proxy.is_healthy = False
        except Exception as e:
            self.logger.debug(f"Proxy {proxy.url} health check failed: {e}")
            proxy.is_healthy = False
    
    async def close(self):
        """Cleanup resources"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
    
    def get_stats(self) -> Dict:
        """Get proxy statistics"""
        if not self.proxies:
            return {'total': 0, 'healthy': 0, 'unhealthy': 0}
        
        healthy = sum(1 for p in self.proxies if p.is_healthy)
        return {
            'total': len(self.proxies),
            'healthy': healthy,
            'unhealthy': len(self.proxies) - healthy,
            'proxies': [
                {
                    'url': p.url,
                    'success_rate': p.success_rate,
                    'is_healthy': p.is_healthy
                }
                for p in self.proxies
            ]
        }
