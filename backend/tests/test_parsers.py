import pytest
import os
import json
from backend.parsers.json_parser import JSONParser
from backend.parsers.csv_parser import CSVParser
from backend.parsers.txt_parser import TXTParser
from backend.parsers.syslog_parser import SyslogParser
from backend.parsers.parser_factory import ParserFactory
from backend.parsers.azure_parser import (
    AzureParser, parse_file, compute_severity, derive_status, derive_category,
)


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


SINGLE_INCIDENT_LOG = """\
=================================================================================
AZURE INFRASTRUCTURE INCIDENT LOG
Environment : Production
Region      : East US
Correlation ID : c6b72d2d-45d1-4b8f-a76f-9b4e33d74f0d
=================================================================================

2026-07-30T09:18:42.174Z INFO UserRequestService
User: john.doe@contoso.com
Action: Create Azure Subscription

------------------------------------------------------------

2026-07-30T09:19:54.173Z ERROR Azure AD Graph API

HTTP Status:
504 Gateway Timeout

Response:
{
   "error":{
      "code":"GatewayTimeout",
      "message":"Directory service unavailable."
   }
}

------------------------------------------------------------

2026-07-30T09:20:38.114Z INFO Incident Recorder

Category:
Azure Subscription Provisioning

Incident Status:
Resolved

=================================================================================
END OF LOG
=================================================================================
"""

MULTI_INCIDENT_LOG = """\
=================================================================================
AZURE INFRASTRUCTURE INCIDENT LOG
Environment : Production
Severity : SEV-1
Correlation ID : dbe29174-9fd7-47cb-a843-8ab26fd81145
=================================================================================
WORKFLOW STARTED
=================================================================================

2026-07-30T14:18:11.203Z INFO Request Service
Status : Accepted

=================================================================================
INCIDENT 1
AZURE SUBSCRIPTION PROVISIONING FAILED
=================================================================================

2026-07-30T14:19:14.281Z ERROR Azure Subscription API
HTTP Status: 504 Gateway Timeout

=================================================================================
INCIDENT 2
RESOURCE GROUP CREATION FAILED
=================================================================================

2026-07-30T14:19:52.617Z ERROR ARM Validation
Error: InvalidTemplate

=================================================================================
ROOT CAUSE ANALYSIS
=================================================================================

Subscription API timed out repeatedly.

=================================================================================
INCIDENT STATUS

OPEN
=================================================================================
END OF LOG
=================================================================================
"""


class TestAzureParser:
    """Azure block-format parser (flat BaseParser interface)."""

    def test_flat_parse_of_single_incident(self):
        events = AzureParser().parse_content(SINGLE_INCIDENT_LOG)

        assert len(events) == 3
        assert events[0]['level'] == 'info'
        assert events[1]['level'] == 'error'
        # HTTP status is surfaced as the error code
        assert events[1]['error_code'] == '504'
        # banner correlation id is attached to every event
        assert all(e['correlation_id'] == 'c6b72d2d-45d1-4b8f-a76f-9b4e33d74f0d' for e in events)

    def test_flat_parse_includes_child_events(self):
        events = AzureParser().parse_content(MULTI_INCIDENT_LOG)
        # 1 framing event + 1 per child incident
        assert len(events) == 3

    def test_factory_returns_azure_parser_for_log(self):
        assert isinstance(ParserFactory.get_parser('log'), AzureParser)


class TestAzureHierarchicalParse:
    """parse_file() — the parent/child structure used by the upload route."""

    def test_single_incident_has_no_children(self):
        parsed = parse_file(SINGLE_INCIDENT_LOG)

        assert parsed.format == 'block'
        assert parsed.children == []
        assert len(parsed.parent_events) == 3
        assert parsed.metadata['Environment'] == 'Production'
        assert parsed.metadata['Region'] == 'East US'
        assert compute_severity(parsed.parent_events) == 'SEV2'
        assert derive_status(parsed) == 'Resolved'
        assert derive_category(parsed) == 'Azure Subscription Provisioning'

    def test_multi_incident_splits_into_children(self):
        parsed = parse_file(MULTI_INCIDENT_LOG)

        assert parsed.format == 'block-hier'
        assert len(parsed.children) == 2
        assert parsed.children[0].index == 1
        assert 'AZURE SUBSCRIPTION PROVISIONING FAILED' in parsed.children[0].name
        assert len(parsed.children[0].events) == 1
        # banner severity wins over computed when stated
        assert parsed.parent_severity == 'SEV1'
        assert derive_status(parsed) == 'Open'
        assert 'timed out repeatedly' in parsed.analysis['root_cause']

    def test_json_payload_is_structured(self):
        parsed = parse_file(SINGLE_INCIDENT_LOG)
        error_event = next(e for e in parsed.parent_events if e.level == 'error')
        payload = error_event.details['_payloads'][0]
        assert payload['error']['code'] == 'GatewayTimeout'

    def test_garbage_input_does_not_raise(self):
        parsed = parse_file(b'\x00\x01 not a log at all \xff')
        assert parsed.children == []
