import asyncio
from typing import Dict, Any, Optional
import httpx
from src.config import settings, get_luma_api_url, validate_api_key
from src.models import APIError
from src.utils.rate_limiter import rate_limit_request


class LumaAPIError(Exception):
    """Custom exception for LUMA API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class LumaClient:
    """Async client for LUMA API interactions."""

    def __init__(self):
        if not validate_api_key():
            raise ValueError("LUMA_API_KEY environment variable is required")

        self.api_key = settings.luma_api_key
        self.timeout = httpx.Timeout(settings.request_timeout_seconds)

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make an authenticated request to the LUMA API with rate limiting and retries."""
        if retry_count > settings.max_retries:
            raise LumaAPIError("Maximum retry attempts exceeded")
        """Make an authenticated request to the LUMA API with rate limiting and retries."""

        # Apply rate limiting
        await rate_limit_request(endpoint, method)

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-luma-api-key": self.api_key
        }

        url = get_luma_api_url(endpoint)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle rate limiting
                if response.status_code == 429:
                    if retry_count < settings.max_retries:
                        # Wait with exponential backoff
                        wait_time = min(settings.retry_backoff_factor ** retry_count, 300)  # Max 5 minutes
                        await asyncio.sleep(wait_time)
                        return await self._make_request(endpoint, method, data, retry_count + 1)
                    else:
                        raise LumaAPIError("Rate limit exceeded and max retries reached", 429)

                # Handle other error responses
                if not response.is_success:
                    error_data = None
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", f"API Error: {response.status_code}")
                    except:
                        error_msg = f"API Error: {response.status_code}"

                    raise LumaAPIError(error_msg, response.status_code, error_data)

                return response.json()

            except httpx.TimeoutException:
                if retry_count < settings.max_retries:
                    wait_time = min(settings.retry_backoff_factor ** retry_count, 300)  # Max 5 minutes
                    await asyncio.sleep(wait_time)
                    return await self._make_request(endpoint, method, data, retry_count + 1)
                else:
                    raise LumaAPIError("Request timeout and max retries reached")

            except httpx.RequestError as e:
                raise LumaAPIError(f"Request failed: {str(e)}")

    # Event CRUD operations
    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new event."""
        return await self._make_request("event/create", "POST", event_data)

    async def get_event(self, event_id: str) -> Dict[str, Any]:
        """Get event details by ID."""
        return await self._make_request(f"event/get/{event_id}")

    async def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing event."""
        return await self._make_request(f"event/update/{event_id}", "PUT", event_data)

    async def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete an event."""
        return await self._make_request(f"event/delete/{event_id}", "DELETE")

    async def list_events(self, **params) -> Dict[str, Any]:
        """List user's events with optional filtering."""
        # Note: LUMA API may not have a direct list endpoint, this might need adjustment
        # based on actual API capabilities
        return await self._make_request("user/events", "GET")

    # User operations
    async def get_user_self(self) -> Dict[str, Any]:
        """Get current user information."""
        return await self._make_request("user/get-self")

    # Ticket operations (for future expansion)
    async def create_ticket_types(self, event_id: str, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create ticket types for an event."""
        return await self._make_request(f"event/ticket-types/create", "POST", {
            "event_id": event_id,
            **ticket_data
        })