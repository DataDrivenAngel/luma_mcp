from typing import List
from fastapi import APIRouter, HTTPException, Depends
from src.luma_client import LumaClient, LumaAPIError
from src.models import (
    EventTemplate,
    EventTemplateType,
    CreateFromTemplateRequest,
    EventResponse,
    APIError
)

router = APIRouter(prefix="/templates", tags=["templates"])

# Predefined event templates
EVENT_TEMPLATES = {
    EventTemplateType.MEETUP: EventTemplate(
        type=EventTemplateType.MEETUP,
        name="Community Meetup",
        description="A casual gathering for community members to connect and share ideas",
        default_duration_hours=2,
        require_rsvp_approval=False,
        is_virtual=False
    ),
    EventTemplateType.WORKSHOP: EventTemplate(
        type=EventTemplateType.WORKSHOP,
        name="Hands-on Workshop",
        description="An interactive learning session with practical exercises",
        default_duration_hours=3,
        require_rsvp_approval=True,
        is_virtual=True
    ),
    EventTemplateType.CONFERENCE: EventTemplate(
        type=EventTemplateType.CONFERENCE,
        name="Professional Conference",
        description="A large-scale professional gathering with multiple speakers and sessions",
        default_duration_hours=8,
        require_rsvp_approval=True,
        is_virtual=False
    ),
    EventTemplateType.SOCIAL_GATHERING: EventTemplate(
        type=EventTemplateType.SOCIAL_GATHERING,
        name="Social Gathering",
        description="A relaxed social event for networking and fun",
        default_duration_hours=4,
        require_rsvp_approval=False,
        is_virtual=False
    ),
    EventTemplateType.WEBINAR: EventTemplate(
        type=EventTemplateType.WEBINAR,
        name="Online Webinar",
        description="A virtual presentation or lecture open to online participants",
        default_duration_hours=1,
        require_rsvp_approval=False,
        is_virtual=True
    )
}


async def get_luma_client() -> LumaClient:
    """Dependency to get LUMA API client."""
    return LumaClient()


@router.get("/", response_model=List[EventTemplate], summary="List Templates")
async def list_templates() -> List[EventTemplate]:
    """
    Get all available event templates.
    """
    return list(EVENT_TEMPLATES.values())


@router.get("/{template_type}", response_model=EventTemplate, summary="Get Template")
async def get_template(template_type: EventTemplateType) -> EventTemplate:
    """
    Get a specific event template by type.

    - **template_type**: The type of template (meetup, workshop, conference, social_gathering, webinar)
    """
    if template_type not in EVENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    return EVENT_TEMPLATES[template_type]


@router.post("/create", response_model=EventResponse, summary="Create Event from Template")
async def create_from_template(
    request: CreateFromTemplateRequest,
    client: LumaClient = Depends(get_luma_client)
) -> EventResponse:
    """
    Create a new event using a predefined template.

    - **template_type**: Template to use for the event
    - **name**: Custom name for the event
    - **start_at**: Start time in ISO 8601 format
    - **timezone**: Timezone identifier
    - **meeting_url**: Meeting URL (for virtual events)
    - **geo_address_json**: Location information (for in-person events)
    """
    if request.template_type not in EVENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = EVENT_TEMPLATES[request.template_type]

    # Calculate end time based on template duration
    from datetime import datetime, timedelta
    try:
        start_time = datetime.fromisoformat(request.start_at.replace('Z', '+00:00'))
        end_time = start_time + timedelta(hours=template.default_duration_hours)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid start_at format: {str(e)}")

    # Build event data from template and request
    event_data = {
        "name": request.name,
        "start_at": request.start_at,
        "timezone": request.timezone,
        "end_at": end_time.isoformat().replace('+00:00', 'Z'),
        "require_rsvp_approval": template.require_rsvp_approval
    }

    # Add location or meeting URL based on template type
    if template.is_virtual and request.meeting_url:
        event_data["meeting_url"] = request.meeting_url
    elif not template.is_virtual and request.geo_address_json:
        event_data["geo_address_json"] = request.geo_address_json.dict()

    try:
        result = await client.create_event(event_data)
        return EventResponse(**result)
    except LumaAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=APIError(error=str(e), code=str(e.status_code)).dict()
        )