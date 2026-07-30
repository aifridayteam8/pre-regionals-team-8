import json
from typing import List, Dict, Any
from .base_parser import BaseParser


class JSONParser(BaseParser):
    """Parser for JSON log files."""
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse JSON log file."""
        events = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            # Handle both single JSON object and JSON lines
            if content.startswith('['):
                # JSON array
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            events.append(self._parse_json_item(item))
                    else:
                        events.append(self._parse_json_item(data))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format: {e}")
            else:
                # JSON lines (one JSON object per line)
                for line in content.split('\n'):
                    if line.strip():
                        try:
                            item = json.loads(line)
                            events.append(self._parse_json_item(item))
                        except json.JSONDecodeError:
                            continue
        
        return events
    
    def _parse_json_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single JSON log item."""
        # Common field mappings
        field_mappings = {
            'timestamp': ['timestamp', 'time', '@timestamp', 'datetime', 'date'],
            'level': ['level', 'severity', 'priority', 'log_level'],
            'message': ['message', 'msg', 'text', 'description'],
            'source': ['source', 'logger', 'logger_name', 'component'],
            'host': ['host', 'hostname', 'server', 'machine'],
            'service': ['service', 'application', 'app', 'program'],
            'error_code': ['error_code', 'err_code', 'status_code', 'code'],
            'correlation_id': ['correlation_id', 'trace_id', 'request_id', 'transaction_id']
        }
        
        normalized = {}
        
        for target_field, source_fields in field_mappings.items():
            value = None
            for source_field in source_fields:
                if source_field in item:
                    value = item[source_field]
                    break
            normalized[target_field] = value
        
        # Include any additional fields
        for key, value in item.items():
            if key not in [f for fields in field_mappings.values() for f in fields]:
                normalized[key] = value
        
        return self.normalize_event(normalized)
