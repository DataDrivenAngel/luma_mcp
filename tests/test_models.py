import pytest
from src.models import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EventTemplate,
    EventTemplateType,
    CreateFromTemplateRequest,
    GeoAddressJson,
    APIError
)


class TestEventModels:
    """Test Pydantic models for events."""

    def test_event_create_request_valid(self):
        """Test creating a valid event creation request."""
        event_data = {
            "name": "Test Event",
            "start_at": "2024-12-31T18:00:00Z",
            "timezone": "America/New_York"
        }
        event = EventCreateRequest(**event_data)
        assert event.name == "Test Event"
        assert event.start_at == "2024-12-31T18:00:00Z"
        assert event.timezone == "America/New_York"
        assert event.require_rsvp_approval is False  # default

    def test_event_create_request_invalid_name(self):
        """Test event creation with invalid name."""
        with pytest.raises(ValueError):
            EventCreateRequest(
                name="",  # Empty name should fail
                start_at="2024-12-31T18:00:00Z",
                timezone="America/New_York"
            )

    def test_geo_address_json(self):
        """Test GeoAddressJson model."""
        geo_data = {
            "type": "google",
            "place_id": "ChIJmQJIxlVYwokRLgeuocVOGVU",
            "description": "Test Location"
        }
        geo = GeoAddressJson(**geo_data)
        assert geo.type == "google"
        assert geo.place_id == "ChIJmQJIxlVYwokRLgeuocVOGVU"
        assert geo.description == "Test Location"

    def test_event_response(self):
        """Test EventResponse model."""
        response_data = {
            "id": "event_123",
            "name": "Test Event",
            "start_at": "2024-12-31T18:00:00Z",
            "timezone": "America/New_York",
            "end_at": "2024-12-31T20:00:00Z",
            "require_rsvp_approval": False,
            "meeting_url": None,
            "geo_address_json": None,
            "status": "published",
            "created_at": "2024-12-01T10:00:00Z",
            "updated_at": "2024-12-01T10:00:00Z"
        }
        event = EventResponse(**response_data)
        assert event.id == "event_123"
        assert event.name == "Test Event"
        assert event.status.value == "published"


class TestTemplateModels:
    """Test Pydantic models for templates."""

    def test_event_template(self):
        """Test EventTemplate model."""
        template_data = {
            "type": "meetup",
            "name": "Community Meetup",
            "description": "A casual gathering",
            "default_duration_hours": 2,
            "require_rsvp_approval": False,
            "is_virtual": False
        }
        template = EventTemplate(**template_data)
        assert template.type == EventTemplateType.MEETUP
        assert template.name == "Community Meetup"
        assert template.default_duration_hours == 2

    def test_create_from_template_request(self):
        """Test CreateFromTemplateRequest model."""
        request_data = {
            "template_type": "workshop",
            "name": "My Workshop",
            "start_at": "2024-12-31T18:00:00Z",
            "timezone": "America/New_York"
        }
        request = CreateFromTemplateRequest(**request_data)
        assert request.template_type == EventTemplateType.WORKSHOP
        assert request.name == "My Workshop"

    def test_api_error(self):
        """Test APIError model."""
        error_data = {
            "error": "Something went wrong",
            "code": "500",
            "details": {"field": "name", "issue": "required"}
        }
        error = APIError(**error_data)
        assert error.error == "Something went wrong"
        assert error.code == "500"
        assert error.details == {"field": "name", "issue": "required"}