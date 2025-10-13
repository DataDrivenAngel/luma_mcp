from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from src.luma_client import LumaClient, LumaAPIError
from src.models import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    APIError
)

router = APIRouter(prefix="/events", tags=["events"])


async def get_luma_client() -> LumaClient:
    """Dependency to get LUMA API client."""
    return LumaClient()


@router.post("/", response_model=EventResponse, summary="Create Event")
async def create_event(
    event: EventCreateRequest,
    client: LumaClient = Depends(get_luma_client)
) -> EventResponse:
    """
    Create a new LUMA event.

    - **name**: Event title (required)
    - **start_at**: Start time in ISO 8601 format (required)
    - **timezone**: Timezone identifier (required)
    - **end_at**: End time in ISO 8601 format (optional)
    - **require_rsvp_approval**: Whether RSVPs need approval (optional)
    - **meeting_url**: URL for virtual events (optional)
    - **geo_address_json**: Location information (optional)
    """
    try:
        result = await client.create_event(event.dict(exclude_unset=True))
        return EventResponse(**result)
    except LumaAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=APIError(error=str(e), code=str(e.status_code)).dict()
        )


@router.get("/{event_id}", response_model=EventResponse, summary="Get Event")
async def get_event(
    event_id: str,
    client: LumaClient = Depends(get_luma_client)
) -> EventResponse:
    """
    Get details of a specific event by ID.

    - **event_id**: The unique identifier of the event
    """
    try:
        result = await client.get_event(event_id)
        return EventResponse(**result)
    except LumaAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Event not found")
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=APIError(error=str(e), code=str(e.status_code)).dict()
        )


@router.put("/{event_id}", response_model=EventResponse, summary="Update Event")
async def update_event(
    event_id: str,
    event_update: EventUpdateRequest,
    client: LumaClient = Depends(get_luma_client)
) -> EventResponse:
    """
    Update an existing event.

    - **event_id**: The unique identifier of the event
    - **event_update**: Fields to update (all optional)
    """
    try:
        result = await client.update_event(
            event_id,
            event_update.dict(exclude_unset=True, exclude_none=True)
        )
        return EventResponse(**result)
    except LumaAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Event not found")
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=APIError(error=str(e), code=str(e.status_code)).dict()
        )


@router.delete("/{event_id}", summary="Delete Event")
async def delete_event(
    event_id: str,
    client: LumaClient = Depends(get_luma_client)
):
    """
    Delete an event.

    - **event_id**: The unique identifier of the event
    """
    try:
        await client.delete_event(event_id)
        return {"message": "Event deleted successfully"}
    except LumaAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Event not found")
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=APIError(error=str(e), code=str(e.status_code)).dict()
        )


@router.get("/", response_model=List[EventResponse], summary="List Events")
async def list_events(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    client: LumaClient = Depends(get_luma_client)
) -> List[EventResponse]:
    """
    List user's events.

    - **limit**: Maximum number of events to return (default: 50, max: 100)
    - **offset**: Number of events to skip (default: 0)
    """
    # Validate input parameters
    if limit is not None and (limit < 1 or limit > 100):
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    if offset is not None and offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    try:
        result = await client.list_events(limit=limit, offset=offset)
        # Assuming the API returns a list or dict with events
        events = result.get("events", result) if isinstance(result, dict) else result
        if not isinstance(events, list):
            raise HTTPException(status_code=500, detail="Invalid response format from LUMA API")
        return [EventResponse(**event) for event in events]
    except LumaAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=APIError(error=str(e), code=str(e.status_code)).dict()
        )