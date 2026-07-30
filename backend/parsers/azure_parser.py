import re
from typing import List, Dict, Any
from .base_parser import BaseParser


class AzureParser(BaseParser):
    """Parser for Azure Infrastructure log format."""
    
    # Pattern for Azure log entries: TIMESTAMP LEVEL SERVICE
    AZURE_PATTERN = r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(?P<level>\w+)\s+(?P<service>.+)'
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Azure Infrastructure log file."""
        events = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse Azure Infrastructure log content from string."""
        events = []
        
        # Split by separator lines
        sections = content.split('------------------------------------------------------------')
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Skip header section
            if 'AZURE INFRASTRUCTURE INCIDENT LOG' in section or 'END OF LOG' in section:
                continue
            
            # Try to parse as a log entry
            event = self._parse_azure_section(section)
            if event:
                events.append(event)
        
        return events
    
    def _parse_azure_section(self, section: str) -> Dict[str, Any]:
        """Parse a single Azure log section."""
        lines = section.split('\n')
        
        # First line should be the header
        if not lines:
            return None
        
        header_line = lines[0].strip()
        match = re.match(self.AZURE_PATTERN, header_line)
        
        if match:
            groups = match.groupdict()
            
            # Combine remaining lines as message
            message = '\n'.join(lines[1:]).strip()
            
            # Extract correlation ID if present
            correlation_id = self._extract_correlation_id(message)
            
            return self.normalize_event({
                'timestamp': groups.get('timestamp'),
                'level': groups.get('level'),
                'service': groups.get('service'),
                'message': message,
                'correlation_id': correlation_id,
                'raw_data': section
            })
        
        return None
    
    def _extract_correlation_id(self, text: str) -> str:
        """Extract correlation ID from text."""
        patterns = [
            r'correlation[_\s]?id[:\s]*([a-f0-9-]{36})',
            r'correlationid[:\s]*([a-f0-9-]{36})',
            r'CorrelationId[:\s]*([a-f0-9-]{36})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
