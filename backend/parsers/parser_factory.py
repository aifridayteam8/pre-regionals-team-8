from backend.parsers.json_parser import JSONParser
from backend.parsers.csv_parser import CSVParser
from backend.parsers.txt_parser import TXTParser
from backend.parsers.syslog_parser import SyslogParser
from backend.parsers.azure_parser import AzureParser


class ParserFactory:
    """Factory class for creating appropriate parser instances."""
    
    @staticmethod
    def get_parser(file_type: str):
        """Get parser based on file type."""
        parsers = {
            'json': JSONParser,
            'csv': CSVParser,
            'txt': TXTParser,
            'log': AzureParser,  # .log files use Azure parser for Azure logs
            'syslog': SyslogParser,
            'azure': AzureParser
        }
        
        parser_class = parsers.get(file_type.lower())
        if not parser_class:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return parser_class()
    
    @staticmethod
    def get_parser_by_filename(filename: str):
        """Get parser based on filename extension."""
        import os
        _, ext = os.path.splitext(filename)
        file_type = ext.lstrip('.')
        return ParserFactory.get_parser(file_type)
