import pytest
import os
import json
from backend.parsers.json_parser import JSONParser
from backend.parsers.csv_parser import CSVParser
from backend.parsers.txt_parser import TXTParser
from backend.parsers.syslog_parser import SyslogParser
from backend.parsers.parser_factory import ParserFactory


class TestJSONParser:
    """Test JSON parser."""
    
    def test_parse_json_array(self, tmp_path):
        """Test parsing JSON array."""
        # Create test file
        data = [
            {"timestamp": "2024-01-01 12:00:00", "level": "error", "message": "Test error"},
            {"timestamp": "2024-01-01 12:01:00", "level": "info", "message": "Test info"}
        ]
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))
        
        parser = JSONParser()
        events = parser.parse(str(test_file))
        
        assert len(events) == 2
        assert events[0]['level'] == 'error'
        assert events[1]['level'] == 'info'
    
    def test_parse_json_lines(self, tmp_path):
        """Test parsing JSON lines."""
        lines = [
            '{"timestamp": "2024-01-01 12:00:00", "level": "error", "message": "Test"}',
            '{"timestamp": "2024-01-01 12:01:00", "level": "info", "message": "Test"}'
        ]
        test_file = tmp_path / "test.jsonl"
        test_file.write_text('\n'.join(lines))
        
        parser = JSONParser()
        events = parser.parse(str(test_file))
        
        assert len(events) == 2


class TestCSVParser:
    """Test CSV parser."""
    
    def test_parse_csv(self, tmp_path):
        """Test parsing CSV file."""
        content = """timestamp,level,message
2024-01-01 12:00:00,error,Test error
2024-01-01 12:01:00,info,Test info"""
        test_file = tmp_path / "test.csv"
        test_file.write_text(content)
        
        parser = CSVParser()
        events = parser.parse(str(test_file))
        
        assert len(events) == 2
        assert events[0]['level'] == 'error'
        assert events[1]['level'] == 'info'


class TestTXTParser:
    """Test TXT parser."""
    
    def test_parse_txt(self, tmp_path):
        """Test parsing text file."""
        content = """2024-01-01 12:00:00 [ERROR] Test error message
2024-01-01 12:01:00 [INFO] Test info message"""
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        parser = TXTParser()
        events = parser.parse(str(test_file))
        
        assert len(events) >= 2


class TestSyslogParser:
    """Test Syslog parser."""
    
    def test_parse_syslog(self, tmp_path):
        """Test parsing syslog format."""
        content = """Jan 30 12:00:00 server1 application: Test message
Jan 30 12:01:00 server2 service: Another message"""
        test_file = tmp_path / "test.log"
        test_file.write_text(content)
        
        parser = SyslogParser()
        events = parser.parse(str(test_file))
        
        assert len(events) >= 2


class TestParserFactory:
    """Test parser factory."""
    
    def test_get_json_parser(self):
        """Test getting JSON parser."""
        parser = ParserFactory.get_parser('json')
        assert isinstance(parser, JSONParser)
    
    def test_get_csv_parser(self):
        """Test getting CSV parser."""
        parser = ParserFactory.get_parser('csv')
        assert isinstance(parser, CSVParser)
    
    def test_get_txt_parser(self):
        """Test getting TXT parser."""
        parser = ParserFactory.get_parser('txt')
        assert isinstance(parser, TXTParser)
    
    def test_get_parser_by_filename(self):
        """Test getting parser by filename."""
        parser = ParserFactory.get_parser_by_filename('test.json')
        assert isinstance(parser, JSONParser)
    
    def test_invalid_parser(self):
        """Test invalid parser type."""
        with pytest.raises(ValueError):
            ParserFactory.get_parser('invalid')
