"""
Tests for the MCP Server core functionality.
"""

import pytest
from fastapi.testclient import TestClient

from industrial_mcp import MCPServer


class TestMCPServerBasics:
    """Test basic MCP server functionality."""
    
    def test_server_creation(self):
        """Test that we can create a server."""
        server = MCPServer(name="test", host="127.0.0.1", port=9000)
        assert server.name == "test"
        assert server.host == "127.0.0.1"
        assert server.port == 9000
    
    def test_server_has_app(self):
        """Test that server creates a FastAPI app."""
        server = MCPServer(name="test")
        assert server._app is not None
    
    def test_tool_registration(self):
        """Test that tools can be registered."""
        server = MCPServer(name="test")
        
        @server.tool("my_tool")
        async def my_tool():
            """A test tool."""
            return {"result": "success"}
        
        assert "my_tool" in server._tools
        assert "my_tool" in server._tool_definitions


class TestMCPServerAPI:
    """Test MCP server HTTP API endpoints."""
    
    def test_root_endpoint(self, test_client: TestClient):
        """Test the root endpoint returns server info."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_list_tools(self, test_client: TestClient):
        """Test listing available tools."""
        response = test_client.get("/mcp/tools")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        # Demo server has registered tools
        assert len(tools) >= 1
    
    def test_tool_has_required_fields(self, test_client: TestClient):
        """Test that tool definitions have required fields."""
        response = test_client.get("/mcp/tools")
        tools = response.json()
        
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
    
    def test_call_tool(self, test_client: TestClient):
        """Test calling a tool."""
        response = test_client.post(
            "/mcp/tools/get_temperature/call",
            json={"sensor_id": "test_sensor"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "temperature" in data
        assert data["sensor_id"] == "test_sensor"
    
    def test_call_nonexistent_tool(self, test_client: TestClient):
        """Test calling a tool that doesn't exist."""
        response = test_client.post(
            "/mcp/tools/nonexistent_tool/call",
            json={}
        )
        assert response.status_code == 404


class TestToolDecorator:
    """Test the @server.tool decorator functionality."""
    
    def test_decorator_preserves_function(self):
        """Test that decorator preserves original function."""
        server = MCPServer(name="test")
        
        @server.tool("test_tool")
        async def test_tool():
            """Test docstring."""
            return {"value": 42}
        
        # Function should still be callable
        import asyncio
        result = asyncio.run(test_tool())
        assert result == {"value": 42}
    
    def test_decorator_uses_docstring(self):
        """Test that decorator uses docstring as description."""
        server = MCPServer(name="test")
        
        @server.tool("documented_tool")
        async def documented_tool():
            """This is the tool description."""
            return {}
        
        definition = server._tool_definitions["documented_tool"]
        assert "This is the tool description" in definition.description
    
    def test_decorator_with_custom_description(self):
        """Test decorator with explicit description."""
        server = MCPServer(name="test")
        
        @server.tool("custom_tool", description="Custom description")
        async def custom_tool():
            """This docstring should be ignored."""
            return {}
        
        definition = server._tool_definitions["custom_tool"]
        assert definition.description == "Custom description"
