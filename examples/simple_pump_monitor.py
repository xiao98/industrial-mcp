"""
Example: Simple predictive maintenance demo with Industrial MCP.

This example shows how to set up an MCP server that monitors
a pump and provides AI-accessible tools for predictive maintenance.

Run with:
    python examples/simple_pump_monitor.py
"""

import asyncio
from industrial_mcp import MCPServer, ModbusAdapter


async def main():
    # Create MCP server
    server = MCPServer(name="pump-monitoring-demo")
    
    # Connect to a Modbus pump controller
    # (Replace with your actual device IP)
    pump = ModbusAdapter(
        host="192.168.1.100",  # Change to your device IP
        port=502,
        device_name="main-pump"
    )
    
    # Register device
    server.register_device(pump)
    
    # Define tools that AI can use
    
    @server.tool("get_pump_temperature")
    async def get_temperature():
        """Get the current temperature of the main pump in Celsius."""
        if not pump._connected:
            await pump.connect()
        
        # Read temperature from register 100
        # (Adjust register address for your device)
        value = await pump.read_register(address=100)
        
        if value is not None:
            # Convert raw value to temperature (example scaling)
            temp_celsius = value / 10.0
            return {
                "temperature": temp_celsius,
                "unit": "°C",
                "status": "normal" if temp_celsius < 80 else "warning"
            }
        return {"error": "Could not read temperature"}
    
    @server.tool("get_pump_vibration")
    async def get_vibration():
        """Get the current vibration level of the pump."""
        if not pump._connected:
            await pump.connect()
        
        value = await pump.read_register(address=101)
        
        if value is not None:
            return {
                "vibration": value,
                "unit": "mm/s",
                "status": "normal" if value < 50 else "warning" if value < 80 else "critical"
            }
        return {"error": "Could not read vibration"}
    
    @server.tool("get_pump_status")
    async def get_full_status():
        """Get comprehensive status of the main pump including all sensors."""
        if not pump._connected:
            await pump.connect()
        
        # Read multiple registers at once
        registers = await pump.read_registers(address=100, count=5)
        
        if registers:
            return {
                "temperature": registers[0] / 10.0,
                "vibration": registers[1],
                "pressure": registers[2] / 100.0,
                "flow_rate": registers[3],
                "running_hours": registers[4],
                "overall_status": "healthy"
            }
        return {"error": "Could not read pump status"}
    
    @server.tool("analyze_maintenance_need")
    async def analyze_maintenance():
        """
        Analyze if the pump needs maintenance based on current readings.
        Returns a recommendation and confidence level.
        """
        if not pump._connected:
            await pump.connect()
        
        temp = await pump.read_register(100)
        vibration = await pump.read_register(101)
        
        # Simple analysis logic (would be ML model in production)
        issues = []
        confidence = 100
        
        if temp and temp / 10.0 > 70:
            issues.append("Elevated temperature detected")
            confidence -= 20
            
        if vibration and vibration > 40:
            issues.append("Abnormal vibration pattern")
            confidence -= 30
        
        if issues:
            return {
                "needs_maintenance": True,
                "urgency": "high" if confidence < 60 else "medium",
                "issues": issues,
                "recommendation": "Schedule inspection within 48 hours",
                "confidence": confidence
            }
        else:
            return {
                "needs_maintenance": False,
                "urgency": "none",
                "issues": [],
                "recommendation": "Continue normal operation",
                "confidence": 95
            }
    
    # Start the server
    print("🏭 Starting Industrial MCP Server...")
    print("📡 Pump monitoring demo")
    print("🔗 Connect your AI client to http://localhost:8080")
    print("")
    print("Available tools:")
    print("  - get_pump_temperature: Read current temperature")
    print("  - get_pump_vibration: Read vibration level")
    print("  - get_pump_status: Get full status")
    print("  - analyze_maintenance_need: AI maintenance analysis")
    print("")
    print("Press Ctrl+C to stop")
    
    server.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    asyncio.run(main())
