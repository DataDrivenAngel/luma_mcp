from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import httpx



# Load environment variables
load_dotenv()

# Configuration
LUMA_API_KEY = os.getenv("LUMA_API_KEY")
LUMA_BASE_URL = "https://api.lu.ma/public/v1"

if not LUMA_API_KEY:
    raise ValueError("LUMA_API_KEY environment variable is required")

# Initialize FastMCP server
mcp = FastMCP("Luma Event Manager")


class LocationData(BaseModel):
    """Location data for events using Google Places."""
    type: str = "google"
    place_id: str
    description: Optional[str] = None


class EventCreateRequest(BaseModel):
    """Request model for creating events."""
    name: str = Field(..., description="Event title")
    start_at: str = Field(..., description="Event start time in ISO 8601 format")
    timezone: str = Field(..., description="Timezone identifier (e.g., 'America/New_York')")
    end_at: Optional[str] = Field(None, description="Event end time in ISO 8601 format")
    require_rsvp_approval: Optional[bool] = Field(False, description="Whether RSVPs need approval")
    meeting_url: Optional[str] = Field(None, description="URL for virtual events")
    geo_address_json: Optional[LocationData] = Field(None, description="Location information")


class EventUpdateRequest(BaseModel):
    """Request model for updating events."""
    name: Optional[str] = Field(None, description="Event title")
    start_at: Optional[str] = Field(None, description="Event start time in ISO 8601 format")
    timezone: Optional[str] = Field(None, description="Timezone identifier")
    end_at: Optional[str] = Field(None, description="Event end time in ISO 8601 format")
    require_rsvp_approval: Optional[bool] = Field(None, description="Whether RSVPs need approval")
    meeting_url: Optional[str] = Field(None, description="URL for virtual events")
    geo_address_json: Optional[LocationData] = Field(None, description="Location information")


class LumaClient:
    """Client for interacting with the Luma API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = LUMA_BASE_URL
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-luma-api-key": api_key
        }
    
    async def make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the Luma API with proper error handling."""

        
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 429:
                    raise Exception("Rate limit exceeded. Please retry after 1 minute.")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    error_data = e.response.json() if e.response.content else {}
                    raise Exception(f"Bad Request: {error_data.get('message', 'Invalid parameters')}")
                elif e.response.status_code == 401:
                    raise Exception("Unauthorized: Check your API key")
                elif e.response.status_code == 500:
                    raise Exception("Server error. Try again later.")
                else:
                    raise Exception(f"API Error: {e.response.status_code}")
            except httpx.RequestError as e:
                raise Exception(f"Network error: {str(e)}")


# Initialize Luma client
luma_client = LumaClient(LUMA_API_KEY)


@mcp.tool()
async def create_event(
    name: str,
    timezone: str,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    require_rsvp_approval: Optional[bool] = False,
    meeting_url: Optional[str] = None,
    place_id: Optional[str] = None,
    location_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Luma event.

    Args:
        name: Event title
        timezone: Timezone identifier (e.g., "America/New_York")
        start_at: Event start time in ISO 8601 format (optional, defaults to 7 days from now)
        end_at: Event end time in ISO 8601 format (optional)
        require_rsvp_approval: Whether RSVPs need approval (default: False)
        meeting_url: URL for virtual events (optional)
        place_id: Google Places ID for location (optional)
        location_description: Description for the location (optional)
    
    Returns:
        Dictionary containing the created event data
    """
    if start_at is None:
        start_at = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

    try:
        # Validate and prepare event data
        event_data = {
            "name": name,
            "start_at": start_at,
            "timezone": timezone
        }
        
        if end_at:
            event_data["end_at"] = end_at
        
        if require_rsvp_approval is not None:
            event_data["require_rsvp_approval"] = require_rsvp_approval
        
        if meeting_url:
            event_data["meeting_url"] = meeting_url
        
        if place_id:
            event_data["geo_address_json"] = {
                "type": "google",
                "place_id": place_id
            }
            if location_description:
                event_data["geo_address_json"]["description"] = location_description
        
        result = await luma_client.make_request("/event/create", "POST", event_data)
        return {"success": True, "event": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_event(event_id: str) -> Dict[str, Any]:
    """
    Get details of a specific Luma event.
    
    Args:
        event_id: The ID of the event to retrieve
    
    Returns:
        Dictionary containing the event data
    """
    try:
        result = await luma_client.make_request(f"/event/get?event_id={event_id}")
        return {"success": True, "event": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def list_events(limit: Optional[int] = 50) -> Dict[str, Any]:
    """
    List events from your Luma calendar.
    
    Args:
        limit: Maximum number of events to return (default: 50)
    
    Returns:
        Dictionary containing a list of events
    """
    try:
        result = await luma_client.make_request(f"/event/list?limit={limit}")
        return {"success": True, "events": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def update_event(
    event_id: str,
    name: Optional[str] = None,
    start_at: Optional[str] = None,
    timezone: Optional[str] = None,
    end_at: Optional[str] = None,
    require_rsvp_approval: Optional[bool] = None,
    meeting_url: Optional[str] = None,
    place_id: Optional[str] = None,
    location_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing Luma event.
    
    Args:
        event_id: The ID of the event to update
        name: New event title (optional)
        start_at: New event start time in ISO 8601 format (optional)
        timezone: New timezone identifier (optional)
        end_at: New event end time in ISO 8601 format (optional)
        require_rsvp_approval: Whether RSVPs need approval (optional)
        meeting_url: New URL for virtual events (optional)
        place_id: New Google Places ID for location (optional)
        location_description: New description for the location (optional)
    
    Returns:
        Dictionary containing the updated event data
    """
    try:
        # Prepare update data with only provided fields
        update_data = {}
        
        if name is not None:
            update_data["name"] = name
        if start_at is not None:
            update_data["start_at"] = start_at
        if timezone is not None:
            update_data["timezone"] = timezone
        if end_at is not None:
            update_data["end_at"] = end_at
        if require_rsvp_approval is not None:
            update_data["require_rsvp_approval"] = require_rsvp_approval
        if meeting_url is not None:
            update_data["meeting_url"] = meeting_url
        
        if place_id is not None:
            update_data["geo_address_json"] = {
                "type": "google",
                "place_id": place_id
            }
            if location_description is not None:
                update_data["geo_address_json"]["description"] = location_description
        
        if not update_data:
            return {"success": False, "error": "No fields provided for update"}
        
        result = await luma_client.make_request(f"/event/update?event_id={event_id}", "POST", update_data)
        return {"success": True, "event": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def delete_event(event_id: str) -> Dict[str, Any]:
    """
    Delete a Luma event.
    
    Args:
        event_id: The ID of the event to delete
    
    Returns:
        Dictionary containing the deletion result
    """
    try:
        result = await luma_client.make_request(f"/event/delete?event_id={event_id}", "POST")
        return {"success": True, "message": "Event deleted successfully", "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_user_info() -> Dict[str, Any]:
    """
    Get information about the authenticated user.
    
    Returns:
        Dictionary containing user information
    """
    try:
        result = await luma_client.make_request("/user/get-self")
        return {"success": True, "user": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
