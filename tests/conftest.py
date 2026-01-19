"""
Pytest configuration and fixtures for Industrial MCP tests.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

from industrial_mcp import MCPServer


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mcp_server() -> MCPServer:
    """Create a basic MCP server for testing."""
    return MCPServer(name="test-server", host="127.0.0.1", port=8888)


@pytest.fixture
def demo_server() -> MCPServer:
    """Create a demo MCP server with sample tools."""
    server = MCPServer(name="demo-server", host="127.0.0.1", port=8889)
    
    @server.tool("get_temperature")
    async def get_temperature(sensor_id: str = "default"):
        """Get temperature reading from a sensor."""
        return {
            "sensor_id": sensor_id,
            "temperature": 25.5,
            "unit": "celsius"
        }
    
    @server.tool("set_valve")
    async def set_valve(valve_id: str, position: int):
        """Set valve position (0-100)."""
        return {
            "valve_id": valve_id,
            "position": position,
            "status": "ok"
        }
    
    return server


@pytest.fixture
def test_client(demo_server: MCPServer) -> TestClient:
    """Create a test client for the demo server."""
    return TestClient(demo_server._app)


class MockAdapter:
    """Mock adapter for testing without real hardware."""
    
    def __init__(self, name: str = "mock"):
        self.name = name
        self.connected = False
        self.data = {}
    
    async def connect(self) -> bool:
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        self.connected = False
    
    async def read(self, address: str) -> any:
        return self.data.get(address, 0)
    
    async def write(self, address: str, value: any) -> bool:
        self.data[address] = value
        return True


@pytest.fixture
def mock_adapter() -> MockAdapter:
    """Create a mock adapter for testing."""
    return MockAdapter()
