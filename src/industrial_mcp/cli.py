"""
Industrial MCP Command Line Interface.

Provides commands for starting the server, testing connections,
and managing the Industrial MCP installation.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


@click.group()
@click.version_option(version="0.1.0", prog_name="industrial-mcp")
def cli():
    """
    Industrial MCP - Bridge between AI and Industrial Equipment.
    
    A Model Context Protocol server for industrial environments,
    enabling AI models to interact with PLCs, sensors, and actuators.
    
    Documentation: https://github.com/xiao98/industrial-mcp
    """
    pass


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
@click.option("--port", "-p", default=8080, type=int, help="Port to listen on")
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to config file")
@click.option("--demo", is_flag=True, help="Run in demo mode with simulated devices")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, config: Optional[str], demo: bool, reload: bool):
    """
    Start the Industrial MCP server.
    
    Examples:
    
        # Start with default settings
        industrial-mcp serve
        
        # Start on custom port with config
        industrial-mcp serve -p 9000 -c config.yaml
        
        # Start in demo mode (simulated devices)
        industrial-mcp serve --demo
    """
    from industrial_mcp import MCPServer
    
    click.echo(click.style("🏭 Industrial MCP Server", fg="cyan", bold=True))
    click.echo(f"   Host: {host}")
    click.echo(f"   Port: {port}")
    
    if demo:
        click.echo(click.style("   Mode: DEMO (simulated devices)", fg="yellow"))
        server = _create_demo_server(host, port)
    elif config:
        click.echo(f"   Config: {config}")
        server = _create_server_from_config(host, port, config)
    else:
        click.echo(click.style("   Mode: Empty (no devices configured)", fg="yellow"))
        server = MCPServer(name="industrial-mcp", host=host, port=port)
    
    click.echo()
    click.echo(f"📡 Server starting at http://{host}:{port}")
    click.echo(f"📚 API docs at http://{host}:{port}/docs")
    click.echo()
    
    try:
        if reload:
            import uvicorn
            uvicorn.run(
                "industrial_mcp.server:create_app",
                host=host,
                port=port,
                reload=True,
                factory=True
            )
        else:
            server.run()
    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped")


@cli.command()
@click.argument("device_type", type=click.Choice(["modbus", "opcua", "mqtt"]))
@click.argument("address")
@click.option("--port", "-p", default=None, type=int, help="Port number")
@click.option("--timeout", "-t", default=5, type=int, help="Connection timeout in seconds")
def ping(device_type: str, address: str, port: Optional[int], timeout: int):
    """
    Test connection to an industrial device.
    
    Examples:
    
        # Test Modbus TCP connection
        industrial-mcp ping modbus 192.168.1.100
        
        # Test OPC UA server
        industrial-mcp ping opcua opc.tcp://192.168.1.100:4840
        
        # Test MQTT broker
        industrial-mcp ping mqtt broker.example.com -p 1883
    """
    click.echo(f"🔍 Testing connection to {device_type.upper()} device...")
    click.echo(f"   Address: {address}")
    if port:
        click.echo(f"   Port: {port}")
    click.echo(f"   Timeout: {timeout}s")
    click.echo()
    
    async def test_connection():
        try:
            if device_type == "modbus":
                from industrial_mcp.adapters import ModbusAdapter
                adapter = ModbusAdapter(
                    name="test",
                    host=address,
                    port=port or 502
                )
            elif device_type == "opcua":
                from industrial_mcp.adapters import OPCUAAdapter
                adapter = OPCUAAdapter(
                    name="test",
                    endpoint=address
                )
            elif device_type == "mqtt":
                from industrial_mcp.adapters import MQTTAdapter
                adapter = MQTTAdapter(
                    name="test",
                    broker=address,
                    port=port or 1883
                )
            else:
                click.echo(click.style("❌ Unknown device type", fg="red"))
                return False
            
            # Try to connect
            result = await asyncio.wait_for(adapter.connect(), timeout=timeout)
            
            if result:
                click.echo(click.style("✅ Connection successful!", fg="green"))
                await adapter.disconnect()
                return True
            else:
                click.echo(click.style("❌ Connection failed", fg="red"))
                return False
                
        except asyncio.TimeoutError:
            click.echo(click.style(f"❌ Connection timed out after {timeout}s", fg="red"))
            return False
        except Exception as e:
            click.echo(click.style(f"❌ Error: {e}", fg="red"))
            return False
    
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)


@cli.command("list-tools")
@click.option("--server", "-s", default="http://localhost:8080", help="MCP server URL")
def list_tools(server: str):
    """
    List all tools available on an MCP server.
    
    Example:
    
        industrial-mcp list-tools
        industrial-mcp list-tools -s http://192.168.1.100:8080
    """
    import httpx
    
    click.echo(f"📋 Fetching tools from {server}...")
    click.echo()
    
    try:
        response = httpx.get(f"{server}/mcp/tools", timeout=10)
        response.raise_for_status()
        tools = response.json()
        
        if not tools:
            click.echo(click.style("No tools registered", fg="yellow"))
            return
        
        click.echo(click.style(f"Found {len(tools)} tools:", fg="green", bold=True))
        click.echo()
        
        for tool in tools:
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            click.echo(f"  🔧 {click.style(name, fg='cyan', bold=True)}")
            click.echo(f"     {description}")
            click.echo()
            
    except httpx.ConnectError:
        click.echo(click.style(f"❌ Cannot connect to {server}", fg="red"))
        click.echo("   Is the server running?")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        click.echo(click.style(f"❌ HTTP error: {e.response.status_code}", fg="red"))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
def version():
    """Show version information."""
    from industrial_mcp import __version__
    
    click.echo(click.style("Industrial MCP", fg="cyan", bold=True))
    click.echo(f"  Version: {__version__}")
    click.echo(f"  Python: {sys.version.split()[0]}")
    click.echo()
    click.echo("  GitHub: https://github.com/xiao98/industrial-mcp")
    click.echo("  License: Apache-2.0")


def _create_demo_server(host: str, port: int):
    """Create a demo server with simulated devices."""
    from industrial_mcp import MCPServer
    import random
    
    server = MCPServer(name="demo-factory", host=host, port=port)
    
    @server.tool("get_pump_temperature")
    async def get_pump_temperature():
        """Get the current temperature of the main pump (simulated)."""
        return {
            "device": "pump_1",
            "temperature": round(45 + random.uniform(-5, 10), 1),
            "unit": "celsius",
            "status": "normal"
        }
    
    @server.tool("get_conveyor_speed")
    async def get_conveyor_speed():
        """Get the current speed of the conveyor belt (simulated)."""
        return {
            "device": "conveyor_main",
            "speed": round(1.5 + random.uniform(-0.2, 0.2), 2),
            "unit": "m/s",
            "status": "running"
        }
    
    @server.tool("get_pressure_sensor")
    async def get_pressure_sensor():
        """Get current pressure reading (simulated)."""
        return {
            "device": "pressure_tank_1",
            "pressure": round(2.5 + random.uniform(-0.3, 0.3), 2),
            "unit": "bar",
            "status": "normal"
        }
    
    @server.tool("diagnose_system")
    async def diagnose_system():
        """Run a comprehensive system diagnostic (simulated)."""
        return {
            "overall_status": "healthy",
            "devices_online": 12,
            "devices_warning": 1,
            "devices_error": 0,
            "last_maintenance": "2026-01-15",
            "next_maintenance": "2026-02-15",
            "recommendations": [
                "Pump bearing shows slight wear - schedule inspection",
                "All other systems operating within normal parameters"
            ]
        }
    
    return server


def _create_server_from_config(host: str, port: int, config_path: str):
    """Create a server from a YAML configuration file."""
    import yaml
    from industrial_mcp import MCPServer
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    server_config = config.get("server", {})
    name = server_config.get("name", "industrial-mcp")
    
    server = MCPServer(name=name, host=host, port=port)
    
    # TODO: Initialize adapters from config
    # This would parse the devices section and create appropriate adapters
    
    return server


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
