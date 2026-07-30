# Sample Incident Log Files

This directory contains sample log files in various formats for testing the AI-Powered Incident Report Generator.

## Available Sample Files

### 1. database_error.json
- **Format**: JSON (JSON Lines)
- **Scenario**: Database connection failure and failover issues
- **Events**: 10 events including connection timeouts, query failures, and failover attempts
- **Use Case**: Testing JSON parser and database-related incident analysis

### 2. api_performance.csv
- **Format**: CSV
- **Scenario**: API gateway performance degradation
- **Events**: 10 events including high response times, timeouts, and backend failures
- **Use Case**: Testing CSV parser and performance incident analysis

### 3. security_incident.txt
- **Format**: Plain text
- **Scenario**: Security breach attempt (brute force and SQL injection)
- **Events**: 10 events including failed logins, brute force detection, and injection attempts
- **Use Case**: Testing text parser and security incident analysis

### 4. system_failure.log
- **Format**: Syslog
- **Scenario**: System-level failures (OOM, service crashes, kernel errors)
- **Events**: 13 events including OOM killer, service failures, and kernel panics
- **Use Case**: Testing syslog parser and infrastructure incident analysis

## How to Use

### Upload via API
```bash
# First, create an incident
curl -X POST http://localhost:5000/api/incidents \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Database Connection Failure",
    "description": "Unable to connect to production database",
    "severity": "high",
    "incident_type": "infrastructure"
  }'

# Upload the log file
curl -X POST http://localhost:5000/api/incidents/1/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@sample_logs/database_error.json"
```

### Generate Report
```bash
curl -X POST http://localhost:5000/api/reports/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": 1,
    "title": "Database Connection Failure Report"
  }'
```

## Creating Custom Sample Files

### JSON Format
```json
{"timestamp": "2024-01-15 10:00:00", "level": "error", "message": "Error message"}
```

### CSV Format
```csv
timestamp,level,message
2024-01-15 10:00:00,error,Error message
```

### Text Format
```
2024-01-15 10:00:00 [ERROR] Error message
```

### Syslog Format
```
Jan 15 10:00:00 server service: Error message
```

## Notes

- All sample files are designed to test different parsing scenarios
- Files contain realistic error scenarios for various incident types
- Use these files to verify log parsing and AI report generation functionality
