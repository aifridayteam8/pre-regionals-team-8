import re
from typing import List, Dict, Any
from .base_parser import BaseParser


class TXTParser(BaseParser):
    """Parser for plain text log files."""
    
    # Common log patterns
    PATTERNS = [
        # Apache/Nginx combined log format
        r'(?P<host>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) \d+',
        # Common application log format
        r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[(?P<level>\w+)\]\s+(?P<message>.*)',
        # Simple timestamp + level + message
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\s]*)\s+(?P<level>\w+)\s+(?P<message>.*)',
        # Syslog format
        r'(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<service>\S+):\s+(?P<message>.*)',
        # Generic log with timestamp
        r'(?P<timestamp>\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+(?P<message>.*)',
    ]
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse plain text log file."""
        events = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    event = self._parse_line(line)
                    if event:
                        events.append(event)
        
        return events
    
    def _parse_line(self, line: str) -> Dict[str, Any]:
        """Parse a single log line."""
        for pattern in self.PATTERNS:
            match = re.match(pattern, line)
            if match:
                groups = match.groupdict()
                return self.normalize_event(groups)
        
        # If no pattern matches, treat as simple message
        return self.normalize_event({
            'message': line,
            'timestamp': None,
            'level': 'info'
        })
