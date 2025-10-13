from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class GeoAddressJson(BaseModel):
    type: str = Field(default="google", description="Address type")
    place_id: str = Field(..., description="Google Places ID")
    description: Optional[str] = Field(None, description="Optional description")


class EventCreateRequest(BaseModel):
    name: str = Field(..., description="Event title", min_length=1, max_length=200)
    start_at: str = Field(..., description="Start time in ISO 8601 format")
    timezone: str = Field(..., description="Timezone identifier (e.g., America/New_York)")
    end_at: Optional[str] = Field(None, description="End time in ISO 8601 format")
    require_rsvp_approval: Optional[bool] = Field(False, description="Whether RSVPs need approval")
    meeting_url: Optional[str] = Field(None, description="URL for virtual events", max_length=2000)
    geo_address_json: Optional[GeoAddressJson] = Field(None, description="Location information")

    class Config:
        # Prevent XSS by ensuring no HTML/script content in strings
        json_encoders = {
            str: lambda v: v.replace('<', '<').replace('>', '>') if isinstance(v, str) else v
        }


class EventUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Event title", min_length=1, max_length=200)
    start_at: Optional[str] = Field(None, description="Start time in ISO 8601 format")
    timezone: Optional[str] = Field(None, description="Timezone identifier")
    end_at: Optional[str] = Field(None, description="End time in ISO 8601 format")
    require_rsvp_approval: Optional[bool] = Field(None, description="Whether RSVPs need approval")
    meeting_url: Optional[str] = Field(None, description="URL for virtual events", max_length=2000)
    geo_address_json: Optional[GeoAddressJson] = Field(None, description="Location information")


class EventResponse(BaseModel):
    id: str = Field(..., description="Event ID")
    name: str = Field(..., description="Event title")
    start_at: str = Field(..., description="Start time")
    timezone: str = Field(..., description="Timezone")
    end_at: Optional[str] = Field(None, description="End time")
    require_rsvp_approval: bool = Field(..., description="RSVP approval required")
    meeting_url: Optional[str] = Field(None, description="Meeting URL")
    geo_address_json: Optional[GeoAddressJson] = Field(None, description="Location")
    status: EventStatus = Field(..., description="Event status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class EventTemplateType(str, Enum):
    MEETUP = "meetup"
    WORKSHOP = "workshop"
    CONFERENCE = "conference"
    SOCIAL_GATHERING = "social_gathering"
    WEBINAR = "webinar"


class EventTemplate(BaseModel):
    type: EventTemplateType = Field(..., description="Template type")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    default_duration_hours: int = Field(..., description="Default event duration in hours")
    require_rsvp_approval: bool = Field(default=False, description="Default RSVP approval setting")
    is_virtual: bool = Field(default=False, description="Whether this is typically a virtual event")


class CreateFromTemplateRequest(BaseModel):
    template_type: EventTemplateType = Field(..., description="Template to use")
    name: str = Field(..., description="Custom event name", min_length=1, max_length=200)
    start_at: str = Field(..., description="Start time in ISO 8601 format")
    timezone: str = Field(..., description="Timezone identifier")
    meeting_url: Optional[str] = Field(None, description="Meeting URL (for virtual events)", max_length=2000)
    geo_address_json: Optional[GeoAddressJson] = Field(None, description="Location (for in-person events)")


class APIError(BaseModel):
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")