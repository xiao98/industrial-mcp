"""
Industrial MCP - Open-source MCP server for industrial equipment.

This package provides a standardized way for AI models to interact with
industrial equipment through the Model Context Protocol (MCP).
"""

from industrial_mcp.server import MCPServer
from industrial_mcp.adapters.modbus import ModbusAdapter
from industrial_mcp.adapters.opcua import OPCUAAdapter
from industrial_mcp.adapters.mqtt import MQTTAdapter

__version__ = "0.1.0"
__author__ = "Industrial MCP Team"

__all__ = [
    "MCPServer",
    "ModbusAdapter", 
    "OPCUAAdapter",
    "MQTTAdapter",
]
