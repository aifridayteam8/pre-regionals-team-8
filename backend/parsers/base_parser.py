from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
import re


class BaseParser(ABC):
    """Base class for log parsers."""
    
    def __init__(self):
        self.events = []
    
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse log file and return list of normalized events."""
        pass
    
    def normalize_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event to standard format."""
        normalized = {
            'timestamp': self._parse_timestamp(raw_event.get('timestamp')),
            'level': self._normalize_level(raw_event.get('level', 'info')),
            'source': raw_event.get('source', 'unknown'),
            'message': raw_event.get('message', ''),
            'raw_data': str(raw_event),
            'host': raw_event.get('host'),
            'service': raw_event.get('service'),
            'error_code': raw_event.get('error_code'),
            'correlation_id': raw_event.get('correlation_id')
        }
        return normalized
    
    def _parse_timestamp(self, timestamp) -> datetime:
        """Parse timestamp to datetime object."""
        if timestamp is None:
            return datetime.utcnow()
        
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, str):
            # Try common timestamp formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%d/%b/%Y:%H:%M:%S',
                '%b %d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue
            
            # Try Unix timestamp
            try:
                return datetime.fromtimestamp(float(timestamp))
            except (ValueError, TypeError):
                pass
        
        return datetime.utcnow()
    
    def _normalize_level(self, level: str) -> str:
        """Normalize log level to standard values."""
        if not level:
            return 'info'
        
        level_map = {
            'debug': 'debug',
            'info': 'info',
            'information': 'info',
            'warn': 'warning',
            'warning': 'warning',
            'error': 'error',
            'err': 'error',
            'critical': 'critical',
            'crit': 'critical',
            'fatal': 'critical',
            'trace': 'debug',
        }
        
        level_lower = level.lower()
        return level_map.get(level_lower, 'info')
    
    def extract_correlation_id(self, message: str) -> str:
        """Extract correlation ID from message."""
        patterns = [
            r'correlation[_-]?id[:\s]*([a-f0-9-]+)',
            r'trace[_-]?id[:\s]*([a-f0-9-]+)',
            r'request[_-]?id[:\s]*([a-f0-9-]+)',
            r'transaction[_-]?id[:\s]*([a-f0-9-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_error_code(self, message: str) -> str:
        """Extract error code from message."""
        patterns = [
            r'error[_-]?code[:\s]*([A-Z0-9_-]+)',
            r'err[_-]?code[:\s]*([A-Z0-9_-]+)',
            r'status[_-]?code[:\s]*(\d{3})',
            r'exception[:\s]*([A-Z][a-zA-Z]+Exception)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
