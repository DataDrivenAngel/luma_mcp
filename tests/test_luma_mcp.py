"""
Test suite for the Luma MCP Server

Run tests with: pytest tests/
"""

import pytest
import os
from unittest.mock import AsyncMock, patch
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

from src.main import (
    create_event,
    get_event,
    list_events,
    update_event,
    delete_event,
    get_user_info,
    LumaClient
)


class TestLumaClient:
    """Test the LumaClient class."""
    
    def test_client_initialization(self):
        """Test that LumaClient initializes correctly."""
        client = LumaClient("test_api_key")
        assert client.api_key == "test_api_key"
        assert client.base_url == "https://api.lu.ma/public/v1"
        assert client.headers["x-luma-api-key"] == "test_api_key"
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful API request."""
        client = LumaClient("test_api_key")
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "test_event_id", "name": "Test Event"}
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            result = await client.make_request("/event/create", "POST", {"name": "Test Event"})
            
            assert result == {"id": "test_event_id", "name": "Test Event"}
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit(self):
        """Test rate limit handling."""
        client = LumaClient("test_api_key")
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 429
            
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                await client.make_request("/event/create", "POST", {"name": "Test Event"})
    
    @pytest.mark.asyncio
    async def test_make_request_bad_request(self):
        """Test bad request handling."""
        client = LumaClient("test_api_key")
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Invalid parameters"}
            
            mock_client.return_value.__aenter__.return_value.request.side_effect = Exception("400 Bad Request")
            
            with pytest.raises(Exception, match="Bad Request"):
                await client.make_request("/event/create", "POST", {"invalid": "data"})


class TestEventOperations:
    """Test event CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_event_success(self):
        """Test successful event creation."""
        with patch("src.main.luma_client.make_request") as mock_request:
            mock_request.return_value = {"id": "test_event_id", "name": "Test Event"}
            
            result = await create_event(
                name="Test Event",
                start_at="2024-01-01T19:00:00Z",
                timezone="America/New_York"
            )
            
            assert result["success"] is True
            assert result["event"]["name"] == "Test Event"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_event_with_location(self):
        """Test event creation with location data."""
        with patch("src.main.luma_client.make_request") as mock_request:
            mock_request.return_value = {"id": "test_event_id", "name": "Test Event"}
            
            result = await create_event(
                name="Test Event",
                start_at="2024-01-01T19:00:00Z",
                timezone="America/New_York",
                place_id="ChIJmQJIxlVYwokRLgeuocVOGVU",
                location_description="Test Location"
            )
            
            assert result["success"] is True
            # Verify the request included location data
            call_args = mock_request.call_args
            assert "geo_address_json" in call_args[0][2]
    
    @pytest.mark.asyncio
    async def test_create_event_error(self):
        """Test event creation error handling."""
        with patch("src.main.luma_client.make_request") as mock_request:
            mock_request.side_effect = Exception("API Error")
            
            result = await create_event(
                name="Test Event",
                start_at="2024-01-01T19:00:00Z",
                timezone="America/New_York"
            )
            
            assert result["success"] is False
            assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_event_success(self):
        """Test successful event retrieval."""
        with patch("src.main.luma_client.make_request") as mock_request:
            mock_request.return_value = {"id": "test_event_id", "name": "Test Event"}
            
            result = await get_event("test_event_id")
            
            assert result["success"] is True
            assert result["event"]["id"] == "test_event_id"
    
    @pytest.mark.asyncio
    async def test_list_events_success(self):
        """Test successful event listing."""
        with patch("src.main.luma_client.make_request") as mock_request:
            mock_request.return_value = [
                {"id": "event1", "name": "Event 1"},
                {"id": "event2", "name": "Event 2"}
            ]
            
            result = await list_events(limit=10)
            
            assert result["success"] is True
            assert len(result["events"]) == 2
    
    @pytest.mark.asyncio
    async def test_update_event_success(self):
        """Test successful event update."""
        with patch("src.main.luma_client.make_request") as mock_request:
            mock_request.return_value = {"id": "test_event_id", "name": "Updated Event"}
            
            result = await update_event(
                event_id="test_event_id",
                name="Updated Event"
            )
            
            assert result["success"] is True
            assert result["event"]["name"] == "Updated Event"
    
    @pytest.mark.asyncio
    async def test_update_event_no_fields(self):
        """Test update with no fields provided."""
        result = await update_event(event_id="test_event_id")
        
        assert result["success"] is False
        assert "No fields provided" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_event_success(self):
        """Test successful event deletion."""
        with patch("src.main.luma_client.make_request") as mock_request:
            mock_request.return_value = {"success": True}
            
            result = await delete_event("test_event_id")
            
            assert result["success"] is True
            assert "deleted successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """Test successful user info retrieval."""
        with patch("src.main.luma_client.make_request") as mock_request:
            mock_request.return_value = {"id": "user123", "name": "Test User"}
            
            result = await get_user_info()
            
            assert result["success"] is True
            assert result["user"]["name"] == "Test User"


@pytest.mark.integration
class TestIntegration:
    """Integration tests that require a real API key."""
    
    @pytest.mark.skipif(not os.getenv("LUMA_API_KEY"), reason="LUMA_API_KEY not set")
    @pytest.mark.asyncio
    async def test_real_api_connection(self):
        """Test connection to real Luma API."""
        result = await get_user_info()
        assert result["success"] is True
        assert "user" in result
