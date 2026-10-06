"""
Rate Limiter Module
Handles rate limiting with support for CTF mode (unlimited requests)
"""

import asyncio
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class RateLimiter:
    """
    Token bucket rate limiter with CTF mode support
    
    In CTF mode, rate limiting is disabled (unlimited requests)
    In normal mode, enforces max_requests per time_window
    """
    
    max_requests: int = 10
    time_window: float = 1.0  # seconds
    ctf_mode: bool = False
    
    def __post_init__(self):
        self.tokens = self.max_requests
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        
        if self.ctf_mode:
            self.max_requests = float('inf')
            self.tokens = float('inf')
    
    async def acquire(self):
        """Acquire a token from the bucket"""
        if self.ctf_mode:
            return  # No limiting in CTF mode
        
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.max_requests,
                self.tokens + elapsed * (self.max_requests / self.time_window)
            )
            
            self.last_update = now
            
            # Wait if no tokens available
            while self.tokens < 1:
                wait_time = (1 - self.tokens) / (self.max_requests / self.time_window)
                await asyncio.sleep(wait_time)
                
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.max_requests,
                    self.tokens + elapsed * (self.max_requests / self.time_window)
                )
                self.last_update = now
            
            # Consume one token
            self.tokens -= 1
    
    async def wait_until_available(self, count: int = 1) -> float:
        """
        Calculate wait time until count tokens are available
        Returns wait time in seconds
        """
        if self.ctf_mode:
            return 0.0
        
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            current_tokens = min(
                self.max_requests,
                self.tokens + elapsed * (self.max_requests / self.time_window)
            )
            
            if current_tokens >= count:
                return 0.0
            
            needed = count - current_tokens
            wait_time = needed / (self.max_requests / self.time_window)
            return wait_time
    
    def get_available_tokens(self) -> float:
        """Get current number of available tokens"""
        if self.ctf_mode:
            return float('inf')
        
        now = time.time()
        elapsed = now - self.last_update
        return min(
            self.max_requests,
            self.tokens + elapsed * (self.max_requests / self.time_window)
        )
    
    def reset(self):
        """Reset the rate limiter"""
        self.tokens = self.max_requests
        self.last_update = time.time()
