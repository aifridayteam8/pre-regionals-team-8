import csv
from typing import List, Dict, Any
from .base_parser import BaseParser


class CSVParser(BaseParser):
    """Parser for CSV log files."""
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV log file."""
        events = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            
            delimiter = self._detect_delimiter(sample)
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row in reader:
                if row:  # Skip empty rows
                    events.append(self._parse_csv_row(row))
        
        return events
    
    def _detect_delimiter(self, sample: str) -> str:
        """Detect CSV delimiter."""
        delimiters = [',', ';', '\t', '|']
        counts = {d: sample.count(d) for d in delimiters}
        return max(counts, key=counts.get)
    
    def _parse_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single CSV row."""
        # Normalize keys to lowercase
        normalized_row = {k.lower().strip(): v for k, v in row.items()}
        
        # Common field mappings
        field_mappings = {
            'timestamp': ['timestamp', 'time', 'datetime', 'date'],
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
                if source_field in normalized_row:
                    value = normalized_row[source_field]
                    break
            normalized[target_field] = value
        
        # Include any additional fields
        for key, value in normalized_row.items():
            if key not in [f for fields in field_mappings.values() for f in fields]:
                normalized[key] = value
        
        return self.normalize_event(normalized)
