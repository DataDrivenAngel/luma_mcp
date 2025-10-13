# LUMA MCP Server

A Model Context Protocol (MCP) server for creating and managing LUMA events. 

## Features

- **Event CRUD Operations**: Create, read, update, delete LUMA events
- **Event Templates**: Pre-built templates for common event types (meetups, workshops, conferences, etc.)

## Quick Start

### Prerequisites

- Python 3.8+
- LUMA Plus subscription with API access
- LUMA API key

### Installation


1. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your LUMA API key
```

2. Run the server:
```bash
python -m src.main
```

The server will start on `http://localhost:8000`.

## Configuration

Create a `.env` file with the following variables:

```env
# Required
LUMA_API_KEY=your_luma_api_key_here

# Optional (defaults provided)
LUMA_HOST=localhost
LUMA_PORT=8000
LUMA_DEBUG=false
```

## API Endpoints

### Events

- `POST /events/` - Create a new event
- `GET /events/{event_id}` - Get event details
- `PUT /events/{event_id}` - Update an event
- `DELETE /events/{event_id}` - Delete an event
- `GET /events/` - List events

### Templates

- `GET /templates/` - List available templates
- `GET /templates/{template_type}` - Get template details
- `POST /templates/create` - Create event from template

### Health Check

- `GET /health` - Service health check

## Event Templates

The server includes predefined templates for common event types:

- **Meetup**: Community gatherings (2 hours, no RSVP approval)


## Usage Examples

### Create an Event

```python
import requests

event_data = {
    "name": "Tech Meetup",
    "start_at": "2024-12-31T18:00:00Z",
    "timezone": "America/New_York",
    "end_at": "2024-12-31T20:00:00Z"
}

response = requests.post("http://localhost:8000/events/", json=event_data)
print(response.json())
```

### Create Event from Template

```python
template_data = {
    "template_type": "workshop",
    "name": "Python Workshop",
    "start_at": "2024-12-31T10:00:00Z",
    "timezone": "America/New_York",
    "meeting_url": "https://zoom.us/j/123456"
}

response = requests.post("http://localhost:8000/templates/create", json=template_data)
print(response.json())
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
isort src/ tests/
```

### API Documentation

When running, visit `http://localhost:8000/docs` for interactive API documentation.

## Rate Limiting

The server implements rate limiting to respect LUMA API limits:

- GET requests: 500 per 5 minutes
- POST requests: 100 per 5 minutes
- Automatic retry with exponential backoff on rate limit errors

## Error Handling

The server provides detailed error responses:

```json
{
  "error": "Rate limit exceeded",
  "code": "429",
  "details": {...}
}
```

## Security

- API keys are stored in environment variables (never in code)
- HTTPS is enforced for all LUMA API requests
- Input validation using Pydantic models with length limits
- CORS disabled in production (server should be accessed directly)
- Error messages don't expose internal system details
- Rate limiting prevents abuse
- Request timeouts prevent hanging connections
