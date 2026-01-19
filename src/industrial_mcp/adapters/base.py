"""
Base adapter class for industrial protocols.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DeviceInfo:
    """Information about a connected device."""
    name: str
    protocol: str
    host: str
    port: int
    connected: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAdapter(ABC):
    """
    Abstract base class for all protocol adapters.
    
    All industrial protocol adapters (Modbus, OPC UA, MQTT, etc.)
    must inherit from this class and implement the required methods.
    """
    
    def __init__(self, host: str, port: int, device_name: str = "device"):
        self.host = host
        self.port = port
        self.device_name = device_name
        self._connected = False
        
    @property
    def info(self) -> DeviceInfo:
        """Get device information."""
        return DeviceInfo(
            name=self.device_name,
            protocol=self.protocol_name,
            host=self.host,
            port=self.port,
            connected=self._connected
        )
    
    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Return the protocol name (e.g., 'modbus', 'opcua')."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the device.
        
        Returns:
            True if connection successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the device."""
        pass
    
    @abstractmethod
    async def read(self, address: Any) -> Any:
        """
        Read data from the device.
        
        Args:
            address: Protocol-specific address to read from.
            
        Returns:
            The value read from the device.
        """
        pass
    
    @abstractmethod
    async def write(self, address: Any, value: Any) -> bool:
        """
        Write data to the device.
        
        Args:
            address: Protocol-specific address to write to.
            value: Value to write.
            
        Returns:
            True if write successful, False otherwise.
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    def __str__(self) -> str:
        return f"{self.protocol_name}://{self.host}:{self.port}/{self.device_name}"
