import re
from typing import List, Dict, Any
from .base_parser import BaseParser


class SyslogParser(BaseParser):
    """Parser for Syslog format logs."""
    
    # RFC3164 Syslog format
    SYSLOG_PATTERN = r'(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<process>\S+)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)'
    
    # RFC5424 Syslog format
    SYSLOG5424_PATTERN = r'<(?P<priority>\d+)>(?P<version>\d+)\s+(?P<timestamp>\S+)\s+(?P<host>\S+)\s+(?P<app>\S+)\s+(?P<proc>\S+)\s+(?P<msgid>\S+)\s+(?P<structured_data>\S+)?\s+(?P<message>.*)'
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Syslog format log file."""
        events = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    event = self._parse_syslog_line(line)
                    if event:
                        events.append(event)
        
        return events
    
    def _parse_syslog_line(self, line: str) -> Dict[str, Any]:
        """Parse a single syslog line."""
        # Try RFC5424 format first
        match = re.match(self.SYSLOG5424_PATTERN, line)
        if match:
            groups = match.groupdict()
            priority = int(groups.get('priority', 0))
            level = self._priority_to_level(priority)
            
            return self.normalize_event({
                'timestamp': groups.get('timestamp'),
                'level': level,
                'host': groups.get('host'),
                'service': groups.get('app'),
                'message': groups.get('message'),
                'raw_data': line
            })
        
        # Try RFC3164 format
        match = re.match(self.SYSLOG_PATTERN, line)
        if match:
            groups = match.groupdict()
            
            return self.normalize_event({
                'timestamp': groups.get('timestamp'),
                'level': 'info',  # RFC3164 doesn't have explicit level
                'host': groups.get('host'),
                'service': groups.get('process'),
                'message': groups.get('message'),
                'raw_data': line
            })
        
        # Fallback to simple parsing
        return self.normalize_event({
            'message': line,
            'timestamp': None,
            'level': 'info',
            'raw_data': line
        })
    
    def _priority_to_level(self, priority: int) -> str:
        """Convert syslog priority to log level."""
        severity = priority & 0x07
        
        level_map = {
            0: 'critical',  # Emergency
            1: 'critical',  # Alert
            2: 'critical',  # Critical
            3: 'error',     # Error
            4: 'warning',   # Warning
            5: 'info',      # Notice
            6: 'info',      # Informational
            7: 'debug'      # Debug
        }
        
        return level_map.get(severity, 'info')
