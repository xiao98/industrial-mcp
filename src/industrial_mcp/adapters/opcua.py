"""
OPC UA protocol adapter for industrial equipment.

OPC UA (Open Platform Communications Unified Architecture) is a 
machine-to-machine communication protocol for industrial automation.
"""

from typing import Any, List, Optional
import asyncio

import structlog
from asyncua import Client, Node
from asyncua.common.subscription import Subscription

from industrial_mcp.adapters.base import BaseAdapter

logger = structlog.get_logger()


class OPCUAAdapter(BaseAdapter):
    """
    OPC UA adapter for industrial equipment.
    
    This adapter allows reading and writing to OPC UA servers,
    which are common in modern industrial automation systems.
    
    Example:
        ```python
        adapter = OPCUAAdapter(
            host="192.168.1.100",
            port=4840,
            device_name="plc-01"
        )
        await adapter.connect()
        
        # Read a node value
        value = await adapter.read("ns=2;i=1234")
        
        # Browse available nodes
        nodes = await adapter.browse()
        ```
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 4840,
        device_name: str = "opcua-device",
        endpoint: str = None,
        security_policy: str = None,
        username: str = None,
        password: str = None,
    ):
        super().__init__(host, port, device_name)
        self.endpoint = endpoint or f"opc.tcp://{host}:{port}"
        self.security_policy = security_policy
        self.username = username
        self.password = password
        self._client: Optional[Client] = None
        self._subscription: Optional[Subscription] = None
        
    @property
    def protocol_name(self) -> str:
        return "opcua"
    
    async def connect(self) -> bool:
        """Establish connection to the OPC UA server."""
        try:
            self._client = Client(url=self.endpoint)
            
            # Configure security if provided
            if self.username and self.password:
                self._client.set_user(self.username)
                self._client.set_password(self.password)
            
            await self._client.connect()
            self._connected = True
            
            logger.info("OPC UA connected", endpoint=self.endpoint)
            return True
            
        except Exception as e:
            logger.error("OPC UA connection error", error=str(e))
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close connection to the OPC UA server."""
        if self._client:
            await self._client.disconnect()
            self._connected = False
            logger.info("OPC UA disconnected", endpoint=self.endpoint)
    
    async def read(self, address: str) -> Any:
        """
        Read a value from an OPC UA node.
        
        Args:
            address: Node ID in OPC UA format (e.g., "ns=2;i=1234" or "ns=2;s=Temperature")
            
        Returns:
            The node value
        """
        if not self._connected or not self._client:
            return None
            
        try:
            node = self._client.get_node(address)
            value = await node.read_value()
            return value
            
        except Exception as e:
            logger.error("OPC UA read error", address=address, error=str(e))
            return None
    
    async def write(self, address: str, value: Any) -> bool:
        """
        Write a value to an OPC UA node.
        
        Args:
            address: Node ID in OPC UA format
            value: Value to write
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected or not self._client:
            return False
            
        try:
            node = self._client.get_node(address)
            await node.write_value(value)
            return True
            
        except Exception as e:
            logger.error("OPC UA write error", address=address, error=str(e))
            return False
    
    async def browse(self, node_id: str = None) -> List[dict]:
        """
        Browse available nodes.
        
        Args:
            node_id: Parent node to browse from (None for root)
            
        Returns:
            List of node information dictionaries
        """
        if not self._connected or not self._client:
            return []
            
        try:
            if node_id:
                parent = self._client.get_node(node_id)
            else:
                parent = self._client.get_root_node()
            
            children = await parent.get_children()
            
            result = []
            for child in children:
                try:
                    name = await child.read_browse_name()
                    result.append({
                        "node_id": str(child.nodeid),
                        "name": name.Name,
                        "namespace": name.NamespaceIndex
                    })
                except:
                    pass
                    
            return result
            
        except Exception as e:
            logger.error("OPC UA browse error", error=str(e))
            return []
    
    async def get_node_info(self, address: str) -> Optional[dict]:
        """
        Get detailed information about a node.
        
        Args:
            address: Node ID
            
        Returns:
            Dictionary with node information
        """
        if not self._connected or not self._client:
            return None
            
        try:
            node = self._client.get_node(address)
            
            name = await node.read_browse_name()
            display_name = await node.read_display_name()
            
            return {
                "node_id": address,
                "name": name.Name,
                "display_name": display_name.Text,
            }
            
        except Exception as e:
            logger.error("OPC UA get info error", error=str(e))
            return None
