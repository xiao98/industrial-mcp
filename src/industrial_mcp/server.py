"""
MCP Server implementation for industrial equipment.

This module provides the main MCPServer class that handles
communication between AI clients and industrial devices.
"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from functools import wraps

import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = structlog.get_logger()


class ToolDefinition(BaseModel):
    """Definition of a tool that AI can call."""
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    

class ToolCallRequest(BaseModel):
    """Request to call a tool."""
    name: str
    arguments: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    """Response from a tool call."""
    success: bool
    result: Any = None
    error: Optional[str] = None


class ResourceDefinition(BaseModel):
    """Definition of a resource that AI can access."""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


@dataclass
class MCPServer:
    """
    MCP Server for industrial equipment.
    
    This server implements the Model Context Protocol to expose
    industrial equipment data and controls to AI clients.
    
    Example:
        ```python
        server = MCPServer(name="my-factory")
        
        @server.tool("get_temperature")
        async def get_temp():
            return {"temperature": 25.5}
            
        server.run()
        ```
    """
    
    name: str
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8080
    
    # Internal state
    _tools: Dict[str, Callable] = field(default_factory=dict)
    _tool_definitions: Dict[str, ToolDefinition] = field(default_factory=dict)
    _resources: Dict[str, ResourceDefinition] = field(default_factory=dict)
    _devices: List[Any] = field(default_factory=list)
    _app: Optional[FastAPI] = field(default=None, init=False)
    
    def __post_init__(self):
        """Initialize the FastAPI application."""
        self._app = FastAPI(
            title=f"Industrial MCP - {self.name}",
            version=self.version,
            description="MCP Server for industrial equipment"
        )
        self._setup_routes()
        
    def _setup_routes(self):
        """Set up API routes for MCP protocol."""
        
        @self._app.get("/")
        async def root():
            return {
                "name": self.name,
                "version": self.version,
                "protocol": "mcp",
                "protocol_version": "2024-11-05"
            }
        
        @self._app.get("/tools")
        async def list_tools():
            """List all available tools."""
            return {
                "tools": [
                    {
                        "name": defn.name,
                        "description": defn.description,
                        "inputSchema": {
                            "type": "object",
                            "properties": defn.parameters
                        }
                    }
                    for defn in self._tool_definitions.values()
                ]
            }
        
        @self._app.post("/tools/call")
        async def call_tool(request: ToolCallRequest):
            """Call a specific tool."""
            if request.name not in self._tools:
                raise HTTPException(404, f"Tool '{request.name}' not found")
            
            try:
                tool_func = self._tools[request.name]
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**request.arguments)
                else:
                    result = tool_func(**request.arguments)
                    
                return ToolCallResponse(success=True, result=result)
                
            except Exception as e:
                logger.error("Tool execution failed", tool=request.name, error=str(e))
                return ToolCallResponse(success=False, error=str(e))
        
        @self._app.get("/resources")
        async def list_resources():
            """List all available resources."""
            return {
                "resources": list(self._resources.values())
            }
        
        @self._app.get("/resources/{uri:path}")
        async def read_resource(uri: str):
            """Read a specific resource."""
            if uri not in self._resources:
                raise HTTPException(404, f"Resource '{uri}' not found")
            
            # TODO: Implement resource reading logic
            return {"uri": uri, "content": "Resource content here"}
        
        @self._app.get("/health")
        async def health():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "devices_connected": len(self._devices)
            }
    
    def tool(self, name: str, description: str = None):
        """
        Decorator to register a function as an MCP tool.
        
        Args:
            name: The name of the tool (used by AI to call it)
            description: Human-readable description of what the tool does
            
        Example:
            ```python
            @server.tool("get_pump_status")
            async def get_status():
                '''Get the current pump status'''
                return {"status": "running"}
            ```
        """
        def decorator(func: Callable):
            # Use docstring as description if not provided
            desc = description or func.__doc__ or f"Tool: {name}"
            
            # Register the tool
            self._tools[name] = func
            self._tool_definitions[name] = ToolDefinition(
                name=name,
                description=desc.strip(),
                parameters={}  # TODO: Extract from type hints
            )
            
            logger.info("Registered tool", name=name)
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def register_device(self, device):
        """
        Register an industrial device adapter.
        
        Args:
            device: A device adapter (ModbusAdapter, OPCUAAdapter, etc.)
        """
        self._devices.append(device)
        logger.info("Registered device", device=str(device))
        
    def register_resource(self, uri: str, name: str, description: str, mime_type: str = "application/json"):
        """
        Register a resource that AI can read.
        
        Args:
            uri: Unique URI for the resource
            name: Human-readable name
            description: What the resource contains
            mime_type: MIME type of the resource content
        """
        self._resources[uri] = ResourceDefinition(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type
        )
        logger.info("Registered resource", uri=uri)
    
    def run(self, host: str = None, port: int = None):
        """
        Start the MCP server.
        
        Args:
            host: Host to bind to (default: 0.0.0.0)
            port: Port to listen on (default: 8080)
        """
        import uvicorn
        
        host = host or self.host
        port = port or self.port
        
        logger.info("Starting Industrial MCP Server", host=host, port=port)
        uvicorn.run(self._app, host=host, port=port)
        
    async def run_async(self, host: str = None, port: int = None):
        """Start the MCP server asynchronously."""
        import uvicorn
        
        host = host or self.host
        port = port or self.port
        
        config = uvicorn.Config(self._app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()
