"""
Data Models
"""

import hashlib
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ScrapResult:
    """Data class for scraped results"""
    url: str
    status: int
    content: str
    headers: Dict[str, str]
    timestamp: str
    size: int
    content_type: str
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = hashlib.md5(self.content.encode()).hexdigest()
