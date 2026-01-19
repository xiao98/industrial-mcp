"""
Tests for protocol adapters.
"""

import pytest

from industrial_mcp.adapters.base import BaseAdapter


class TestMockAdapter:
    """Test the mock adapter functionality."""
    
    @pytest.mark.asyncio
    async def test_connect(self, mock_adapter):
        """Test adapter connection."""
        assert not mock_adapter.connected
        result = await mock_adapter.connect()
        assert result is True
        assert mock_adapter.connected
    
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_adapter):
        """Test adapter disconnection."""
        await mock_adapter.connect()
        await mock_adapter.disconnect()
        assert not mock_adapter.connected
    
    @pytest.mark.asyncio
    async def test_read_write(self, mock_adapter):
        """Test read and write operations."""
        await mock_adapter.connect()
        
        # Write a value
        result = await mock_adapter.write("address_1", 42)
        assert result is True
        
        # Read it back
        value = await mock_adapter.read("address_1")
        assert value == 42
    
    @pytest.mark.asyncio
    async def test_read_unset_address(self, mock_adapter):
        """Test reading an address that was never written."""
        await mock_adapter.connect()
        value = await mock_adapter.read("nonexistent")
        assert value == 0  # Default value


class TestBaseAdapter:
    """Test the BaseAdapter abstract class."""
    
    def test_cannot_instantiate_directly(self):
        """Test that BaseAdapter cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseAdapter(name="test")
    
    def test_subclass_must_implement_methods(self):
        """Test that subclasses must implement required methods."""
        
        class IncompleteAdapter(BaseAdapter):
            pass
        
        with pytest.raises(TypeError):
            IncompleteAdapter(name="test")
    
    def test_proper_subclass(self):
        """Test that a properly implemented subclass works."""
        
        class ProperAdapter(BaseAdapter):
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self) -> None:
                pass
            
            async def read(self, address: str):
                return 0
            
            async def write(self, address: str, value) -> bool:
                return True
            
            def get_info(self) -> dict:
                return {"name": self.name}
        
        adapter = ProperAdapter(name="proper")
        assert adapter.name == "proper"


class TestModbusAdapter:
    """Test Modbus adapter (mocked, no real hardware)."""
    
    def test_modbus_adapter_creation(self):
        """Test creating a Modbus adapter."""
        from industrial_mcp.adapters import ModbusAdapter
        
        adapter = ModbusAdapter(
            name="test_modbus",
            host="192.168.1.100",
            port=502
        )
        
        assert adapter.name == "test_modbus"
        assert adapter.host == "192.168.1.100"
        assert adapter.port == 502
    
    def test_modbus_adapter_info(self):
        """Test Modbus adapter info method."""
        from industrial_mcp.adapters import ModbusAdapter
        
        adapter = ModbusAdapter(
            name="test_modbus",
            host="192.168.1.100",
            port=502
        )
        
        info = adapter.get_info()
        assert info["name"] == "test_modbus"
        assert info["protocol"] == "modbus"


class TestOPCUAAdapter:
    """Test OPC UA adapter (mocked, no real server)."""
    
    def test_opcua_adapter_creation(self):
        """Test creating an OPC UA adapter."""
        from industrial_mcp.adapters import OPCUAAdapter
        
        adapter = OPCUAAdapter(
            name="test_opcua",
            endpoint="opc.tcp://192.168.1.100:4840"
        )
        
        assert adapter.name == "test_opcua"
        assert adapter.endpoint == "opc.tcp://192.168.1.100:4840"


class TestMQTTAdapter:
    """Test MQTT adapter (mocked, no real broker)."""
    
    def test_mqtt_adapter_creation(self):
        """Test creating an MQTT adapter."""
        from industrial_mcp.adapters import MQTTAdapter
        
        adapter = MQTTAdapter(
            name="test_mqtt",
            broker="mqtt.example.com",
            port=1883
        )
        
        assert adapter.name == "test_mqtt"
        assert adapter.broker == "mqtt.example.com"
        assert adapter.port == 1883
