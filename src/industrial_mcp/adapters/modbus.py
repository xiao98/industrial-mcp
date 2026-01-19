"""
Modbus protocol adapter for industrial equipment.

Supports both Modbus TCP and Modbus RTU protocols.
"""

from typing import Any, List, Optional, Union
import asyncio

import structlog
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from industrial_mcp.adapters.base import BaseAdapter

logger = structlog.get_logger()


class ModbusAdapter(BaseAdapter):
    """
    Modbus TCP/RTU adapter for industrial equipment.
    
    This adapter allows reading and writing to Modbus devices,
    including PLCs, sensors, meters, and other industrial equipment.
    
    Example:
        ```python
        # TCP connection
        adapter = ModbusAdapter(host="192.168.1.100", port=502)
        await adapter.connect()
        
        # Read holding register
        value = await adapter.read_register(address=100)
        
        # Read multiple registers
        values = await adapter.read_registers(address=100, count=10)
        
        # Write to register
        await adapter.write_register(address=100, value=42)
        ```
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 502,
        device_name: str = "modbus-device",
        unit_id: int = 1,
        mode: str = "tcp",  # "tcp" or "rtu"
        # RTU-specific options
        serial_port: str = None,
        baudrate: int = 9600,
        timeout: float = 3.0,
    ):
        super().__init__(host, port, device_name)
        self.unit_id = unit_id
        self.mode = mode
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout
        self._client = None
        
    @property
    def protocol_name(self) -> str:
        return f"modbus-{self.mode}"
    
    async def connect(self) -> bool:
        """Establish connection to the Modbus device."""
        try:
            if self.mode == "tcp":
                self._client = AsyncModbusTcpClient(
                    host=self.host,
                    port=self.port,
                    timeout=self.timeout
                )
            else:  # RTU
                self._client = AsyncModbusSerialClient(
                    port=self.serial_port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
            
            connected = await self._client.connect()
            self._connected = connected
            
            if connected:
                logger.info("Modbus connected", host=self.host, port=self.port)
            else:
                logger.warning("Modbus connection failed", host=self.host)
                
            return connected
            
        except Exception as e:
            logger.error("Modbus connection error", error=str(e))
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close connection to the Modbus device."""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Modbus disconnected", host=self.host)
    
    async def read(self, address: int) -> Any:
        """Read a single holding register."""
        return await self.read_register(address)
    
    async def write(self, address: int, value: int) -> bool:
        """Write a value to a holding register."""
        return await self.write_register(address, value)
    
    async def read_register(self, address: int, unit_id: int = None) -> Optional[int]:
        """
        Read a single holding register.
        
        Args:
            address: Register address (0-based)
            unit_id: Modbus unit ID (default: instance default)
            
        Returns:
            Register value or None if error
        """
        if not self._connected:
            logger.warning("Modbus not connected")
            return None
            
        try:
            unit = unit_id or self.unit_id
            result = await self._client.read_holding_registers(
                address=address,
                count=1,
                slave=unit
            )
            
            if result.isError():
                logger.error("Modbus read error", address=address, error=str(result))
                return None
                
            return result.registers[0]
            
        except ModbusException as e:
            logger.error("Modbus exception", error=str(e))
            return None
    
    async def read_registers(
        self, 
        address: int, 
        count: int = 1, 
        unit_id: int = None
    ) -> Optional[List[int]]:
        """
        Read multiple holding registers.
        
        Args:
            address: Starting register address
            count: Number of registers to read
            unit_id: Modbus unit ID
            
        Returns:
            List of register values or None if error
        """
        if not self._connected:
            return None
            
        try:
            unit = unit_id or self.unit_id
            result = await self._client.read_holding_registers(
                address=address,
                count=count,
                slave=unit
            )
            
            if result.isError():
                return None
                
            return list(result.registers)
            
        except ModbusException:
            return None
    
    async def write_register(
        self, 
        address: int, 
        value: int, 
        unit_id: int = None
    ) -> bool:
        """
        Write a value to a single holding register.
        
        Args:
            address: Register address
            value: Value to write (16-bit integer)
            unit_id: Modbus unit ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            return False
            
        try:
            unit = unit_id or self.unit_id
            result = await self._client.write_register(
                address=address,
                value=value,
                slave=unit
            )
            
            return not result.isError()
            
        except ModbusException:
            return False
    
    async def read_coils(
        self, 
        address: int, 
        count: int = 1, 
        unit_id: int = None
    ) -> Optional[List[bool]]:
        """Read coil status (discrete outputs)."""
        if not self._connected:
            return None
            
        try:
            unit = unit_id or self.unit_id
            result = await self._client.read_coils(
                address=address,
                count=count,
                slave=unit
            )
            
            if result.isError():
                return None
                
            return list(result.bits[:count])
            
        except ModbusException:
            return None
    
    async def read_input_registers(
        self,
        address: int,
        count: int = 1,
        unit_id: int = None
    ) -> Optional[List[int]]:
        """Read input registers (read-only analog inputs)."""
        if not self._connected:
            return None
            
        try:
            unit = unit_id or self.unit_id
            result = await self._client.read_input_registers(
                address=address,
                count=count,
                slave=unit
            )
            
            if result.isError():
                return None
                
            return list(result.registers)
            
        except ModbusException:
            return None
