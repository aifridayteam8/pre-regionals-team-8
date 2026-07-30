# AI-Powered Incident Report Generator Backend

A production-ready backend for an AI-powered Incident Report Generator using Flask and free/open-source technologies. This system automatically parses incident logs, correlates events, and generates comprehensive AI-powered incident reports using local LLMs (Ollama).

## Features

- **User Authentication**: JWT-based authentication with role-based access control
- **Log Parsing**: Support for JSON, TXT, CSV, and Syslog formats
- **Event Correlation**: Automatic correlation and normalization of log events
- **AI Report Generation**: Local LLM-powered report generation using Ollama
- **Report Management**: Create, edit, save, and download incident reports
- **Analytics Dashboard**: APIs for incident metrics and trends
- **REST API**: Well-documented REST APIs with Swagger UI
- **Database Support**: SQLite (default) and PostgreSQL support
- **Docker Support**: Complete Docker and Docker Compose setup

## Technology Stack

### Backend
- Python 3.12
- Flask
- Flask-RESTX (REST APIs and Swagger documentation)
- Flask-JWT-Extended (JWT Authentication)
- SQLAlchemy (ORM)
- Flask-Migrate (Alembic migrations)
- Marshmallow (serialization/validation)
- Flask-CORS

### Database
- SQLite (default)
- PostgreSQL (optional)

### AI/LLM
- Ollama (local LLM)
- LangChain (optional)
- Support for Llama 3.2, Mistral, Gemma, Phi-3
- Optional OpenAI support via configuration

### Storage
- Local file system for uploaded logs and generated reports

### Testing
- pytest
- unittest.mock

### Deployment
- Docker
- Docker Compose

## Project Structure

```
project/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
├── README.md                  # This file
│
├── routes/                    # API routes
│   ├── __init__.py
│   ├── auth_routes.py         # Authentication endpoints
│   ├── incident_routes.py     # Incident management endpoints
│   ├── report_routes.py       # Report management endpoints
│   └── analytics_routes.py    # Analytics endpoints
│
├── models/                    # Database models
│   ├── __init__.py
│   ├── user.py               # User model
│   ├── incident.py           # Incident and IncidentEvent models
│   └── report.py             # Report model
│
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── incident_service.py   # Incident business logic
│   ├── report_service.py     # Report business logic
│   └── event_service.py      # Event business logic
│
├── ai/                        # AI/LLM integration
│   ├── __init__.py
│   ├── ollama_client.py      # Ollama client
│   ├── openai_client.py      # OpenAI client (optional)
│   └── report_generator.py   # Report generation logic
│
├── parsers/                   # Log parsers
│   ├── __init__.py
│   ├── base_parser.py        # Base parser class
│   ├── json_parser.py        # JSON parser
│   ├── csv_parser.py         # CSV parser
│   ├── txt_parser.py         # Text parser
│   ├── syslog_parser.py      # Syslog parser
│   └── parser_factory.py     # Parser factory
│
├── analytics/                 # Analytics module
│   └── __init__.py
│
├── auth/                      # Authentication module
│   ├── __init__.py
│   ├── jwt_handler.py        # JWT configuration
│   └── decorators.py         # Authentication decorators
│
├── middleware/                # Middleware
│   ├── __init__.py
│   ├── error_handler.py      # Error handling
│   └── request_logger.py     # Request logging
│
├── utils/                     # Utilities
│   ├── __init__.py
│   ├── schemas.py           # Marshmallow schemas
│   └── validators.py        # Custom validators
│
├── uploads/                   # Uploaded log files
├── reports/                   # Generated reports
├── tests/                     # Unit tests
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_models.py       # Model tests
│   └── test_parsers.py      # Parser tests
│
├── migrations/                # Database migrations
├── static/                    # Static files
└── templates/                 # HTML templates
```

## Installation

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Ollama (for local LLM support) - optional but recommended
- Docker and Docker Compose (optional)

### Local Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd pre-regionals-team-8
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize Ollama (for local LLM)**
```bash
# Install Ollama from https://ollama.ai
# Pull a model
ollama pull llama3.2
```

6. **Initialize database**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

7. **Run the application**
```bash
python app.py
```

The API will be available at `http://localhost:5000`
Swagger documentation at `http://localhost:5000/api/docs`

### Docker Installation

1. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

This will start:
- Flask application on port 5000
- PostgreSQL database on port 5432
- Ollama service on port 11434

2. **Pull Ollama model inside container**
```bash
docker-compose exec ollama ollama pull llama3.2
```

3. **Initialize database migrations**
```bash
docker-compose exec app flask db upgrade
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///incident_reports_dev.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost/incident_reports

# AI Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
# Optional OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
USE_OPENAI=false

# CORS Configuration
CORS_ORIGINS=*

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=app.log
```

## API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepassword123"
}
```

#### Refresh Token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

### Incident Endpoints

#### List Incidents
```http
GET /api/incidents?page=1&per_page=20&severity=high&status=open
Authorization: Bearer <access_token>
```

#### Create Incident
```http
POST /api/incidents
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Database Connection Failure",
  "description": "Unable to connect to production database",
  "severity": "high",
  "status": "open",
  "incident_type": "infrastructure",
  "source": "monitoring"
}
```

#### Get Incident
```http
GET /api/incidents/{incident_id}
Authorization: Bearer <access_token>
```

#### Update Incident
```http
PUT /api/incidents/{incident_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "resolved",
  "severity": "medium"
}
```

#### Upload Log File
```http
POST /api/incidents/{incident_id}/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <log_file>
```

#### Get Incident Events
```http
GET /api/incidents/{incident_id}/events?page=1&per_page=100&level=error
Authorization: Bearer <access_token>
```

### Report Endpoints

#### List Reports
```http
GET /api/reports?page=1&per_page=20&status=draft
Authorization: Bearer <access_token>
```

#### Generate Report
```http
POST /api/reports/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "incident_id": 1,
  "title": "Database Connection Failure Report"
}
```

#### Get Report
```http
GET /api/reports/{report_id}
Authorization: Bearer <access_token>
```

#### Update Report
```http
PUT /api/reports/{report_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "executive_summary": "Updated summary",
  "status": "final"
}
```

#### Download Report
```http
GET /api/reports/{report_id}/download?format=markdown
Authorization: Bearer <access_token>
```

### Analytics Endpoints

#### Dashboard Analytics
```http
GET /api/analytics/dashboard?days=30
Authorization: Bearer <access_token>
```

#### Incident Timeline
```http
GET /api/analytics/incidents/timeline?days=30
Authorization: Bearer <access_token>
```

#### Report Performance
```http
GET /api/analytics/reports/performance?days=30
Authorization: Bearer <access_token>
```

#### Events Summary
```http
GET /api/analytics/events/summary?days=30
Authorization: Bearer <access_token>
```

## AI Report Structure

Generated reports include the following sections:

- **Executive Summary**: High-level overview of the incident
- **Incident Overview**: Detailed description and technical details
- **Timeline**: Chronological sequence of events
- **Root Cause Analysis**: Analysis of the primary cause
- **Impact Assessment**: Business, technical, and user impact
- **Systems Affected**: List of affected components
- **Resolution Steps**: Actions taken to resolve the incident
- **Recommendations**: Short-term and long-term recommendations
- **Preventive Actions**: Measures to prevent recurrence
- **Lessons Learned**: Key takeaways from the incident
- **Confidence Score**: AI confidence in the analysis (0.0-1.0)

## Supported Log Formats

### JSON
```json
{"timestamp": "2024-01-01 12:00:00", "level": "error", "message": "Connection failed"}
```

### CSV
```csv
timestamp,level,message
2024-01-01 12:00:00,error,Connection failed
```

### TXT
```
2024-01-01 12:00:00 [ERROR] Connection failed
```

### Syslog
```
Jan 30 12:00:00 server1 application: Connection failed
```

## Testing

### Run Unit Tests
```bash
pytest tests/
```

### Run with Coverage
```bash
pytest --cov=. tests/
```

### Run Specific Test File
```bash
pytest tests/test_models.py
```

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions focused and small

### Adding New Features
1. Create/modify models in `models/`
2. Add business logic in `services/`
3. Create API endpoints in `routes/`
4. Add validation schemas in `utils/schemas.py`
5. Write unit tests in `tests/`
6. Update documentation

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

## Deployment

### Production Considerations

1. **Security**
   - Change all secret keys in production
   - Use HTTPS
   - Enable rate limiting
   - Use environment-specific configurations

2. **Database**
   - Use PostgreSQL for production
   - Set up regular backups
   - Configure connection pooling

3. **AI/LLM**
   - Ensure Ollama service is properly configured
   - Consider using a dedicated server for LLM
   - Monitor resource usage

4. **Monitoring**
   - Set up application monitoring
   - Configure log aggregation
   - Monitor API response times

### Docker Deployment
```bash
# Build production image
docker build -t incident-report-generator:prod .

# Run with production configuration
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e DATABASE_URL=postgresql://... \
  incident-report-generator:prod
```

## Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check Ollama status: `ollama list`
- Verify model is downloaded: `ollama pull llama3.2`

### Database Issues
- Check database URL in `.env`
- Ensure migrations are applied: `flask db upgrade`
- For PostgreSQL, verify connection credentials

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version (requires 3.12+)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at `/api/docs`

## Acknowledgments

- Flask and Flask-RESTX for the web framework
- Ollama for local LLM support
- The open-source community