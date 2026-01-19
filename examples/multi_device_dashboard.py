"""
Multi-Device Factory Dashboard Example

This example demonstrates how to:
1. Connect to multiple industrial devices simultaneously
2. Create a unified monitoring interface
3. Implement basic alerting logic
4. Expose predictive maintenance insights via MCP

Run with:
    python examples/multi_device_dashboard.py
    
Then access:
    http://localhost:8080/docs  - API documentation
    http://localhost:8080/mcp/tools  - Available AI tools
"""

import asyncio
import random
from datetime import datetime
from typing import Dict, List

from industrial_mcp import MCPServer
from industrial_mcp.adapters import ModbusAdapter, OPCUAAdapter, MQTTAdapter


# =============================================================================
# Configuration
# =============================================================================

DEVICES = {
    "pump_station": {
        "type": "modbus",
        "host": "192.168.1.10",
        "port": 502,
        "registers": {
            "temperature": 40001,
            "pressure": 40002,
            "flow_rate": 40003,
            "vibration": 40004,
        }
    },
    "conveyor_line": {
        "type": "modbus", 
        "host": "192.168.1.11",
        "port": 502,
        "registers": {
            "speed": 40001,
            "motor_current": 40002,
            "belt_tension": 40003,
        }
    },
    "temperature_sensors": {
        "type": "mqtt",
        "broker": "mqtt.factory.local",
        "topics": [
            "sensors/zone1/temperature",
            "sensors/zone2/temperature",
            "sensors/zone3/temperature",
        ]
    },
    "scada_system": {
        "type": "opcua",
        "endpoint": "opc.tcp://192.168.1.100:4840",
        "nodes": {
            "production_count": "ns=2;s=Production.Count",
            "quality_score": "ns=2;s=Quality.Score",
            "energy_consumption": "ns=2;s=Energy.kWh",
        }
    }
}

# Alert thresholds
THRESHOLDS = {
    "temperature": {"warning": 70, "critical": 85},
    "vibration": {"warning": 4.0, "critical": 7.0},
    "pressure": {"warning": 8.0, "critical": 10.0},
}


# =============================================================================
# Simulated Data (for demo without real hardware)
# =============================================================================

class SimulatedFactory:
    """Simulates factory data for demonstration."""
    
    def __init__(self):
        self.base_values = {
            "pump_temperature": 55,
            "pump_pressure": 5.5,
            "pump_flow_rate": 120,
            "pump_vibration": 2.5,
            "conveyor_speed": 1.5,
            "motor_current": 12.0,
            "belt_tension": 85,
            "zone1_temp": 22,
            "zone2_temp": 24,
            "zone3_temp": 21,
            "production_count": 15420,
            "quality_score": 98.5,
            "energy_consumption": 1250,
        }
        self.production_count = 15420
    
    def read(self, metric: str) -> float:
        """Read a simulated metric value with some noise."""
        base = self.base_values.get(metric, 0)
        noise = random.uniform(-0.05, 0.05) * base
        
        # Special handling for counter
        if metric == "production_count":
            self.production_count += random.randint(0, 3)
            return self.production_count
        
        return round(base + noise, 2)


# Global simulator instance
simulator = SimulatedFactory()


# =============================================================================
# Create MCP Server
# =============================================================================

server = MCPServer(
    name="smart-factory-dashboard",
    port=8080
)


# =============================================================================
# Register Tools
# =============================================================================

@server.tool("get_factory_overview")
async def get_factory_overview():
    """
    Get a comprehensive overview of the entire factory status.
    Returns data from all connected devices and systems.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "factory_name": "Demo Smart Factory",
        "systems": {
            "pump_station": {
                "status": "running",
                "temperature": simulator.read("pump_temperature"),
                "pressure": simulator.read("pump_pressure"),
                "flow_rate": simulator.read("pump_flow_rate"),
                "vibration": simulator.read("pump_vibration"),
            },
            "conveyor_line": {
                "status": "running",
                "speed": simulator.read("conveyor_speed"),
                "motor_current": simulator.read("motor_current"),
                "belt_tension": simulator.read("belt_tension"),
            },
            "production": {
                "count_today": simulator.read("production_count"),
                "quality_score": simulator.read("quality_score"),
                "energy_kwh": simulator.read("energy_consumption"),
            },
            "environment": {
                "zone1_temperature": simulator.read("zone1_temp"),
                "zone2_temperature": simulator.read("zone2_temp"),
                "zone3_temperature": simulator.read("zone3_temp"),
            }
        }
    }


@server.tool("check_alerts")
async def check_alerts():
    """
    Check all systems for warnings and critical alerts.
    Returns any conditions that exceed defined thresholds.
    """
    alerts = []
    
    # Check pump temperature
    temp = simulator.read("pump_temperature")
    if temp > THRESHOLDS["temperature"]["critical"]:
        alerts.append({
            "severity": "critical",
            "device": "pump_station",
            "metric": "temperature",
            "value": temp,
            "threshold": THRESHOLDS["temperature"]["critical"],
            "message": f"Pump temperature critically high: {temp}°C"
        })
    elif temp > THRESHOLDS["temperature"]["warning"]:
        alerts.append({
            "severity": "warning",
            "device": "pump_station", 
            "metric": "temperature",
            "value": temp,
            "threshold": THRESHOLDS["temperature"]["warning"],
            "message": f"Pump temperature elevated: {temp}°C"
        })
    
    # Check vibration
    vibration = simulator.read("pump_vibration")
    if vibration > THRESHOLDS["vibration"]["critical"]:
        alerts.append({
            "severity": "critical",
            "device": "pump_station",
            "metric": "vibration",
            "value": vibration,
            "threshold": THRESHOLDS["vibration"]["critical"],
            "message": f"Pump vibration critically high: {vibration}mm/s"
        })
    elif vibration > THRESHOLDS["vibration"]["warning"]:
        alerts.append({
            "severity": "warning",
            "device": "pump_station",
            "metric": "vibration", 
            "value": vibration,
            "threshold": THRESHOLDS["vibration"]["warning"],
            "message": f"Pump vibration elevated: {vibration}mm/s"
        })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_alerts": len(alerts),
        "critical_count": len([a for a in alerts if a["severity"] == "critical"]),
        "warning_count": len([a for a in alerts if a["severity"] == "warning"]),
        "alerts": alerts
    }


@server.tool("predict_maintenance")
async def predict_maintenance(device: str = "pump_station"):
    """
    Analyze device data to predict maintenance needs.
    Uses historical patterns and current readings to estimate
    remaining useful life and recommend preventive actions.
    
    Args:
        device: Name of the device to analyze (default: pump_station)
    """
    # Simulated predictive maintenance analysis
    temperature = simulator.read("pump_temperature")
    vibration = simulator.read("pump_vibration")
    
    # Simple degradation score (in real system, use ML model)
    temp_factor = min(temperature / 100, 1.0)
    vib_factor = min(vibration / 10, 1.0)
    degradation_score = (temp_factor * 0.4 + vib_factor * 0.6) * 100
    
    # Estimate remaining useful life
    if degradation_score < 30:
        rul_days = random.randint(180, 365)
        status = "excellent"
        recommendations = ["No immediate action required", "Continue regular monitoring"]
    elif degradation_score < 50:
        rul_days = random.randint(90, 180)
        status = "good"
        recommendations = ["Schedule routine inspection in 30 days", "Monitor vibration trends"]
    elif degradation_score < 70:
        rul_days = random.randint(30, 90)
        status = "fair"
        recommendations = [
            "Schedule maintenance within 2 weeks",
            "Inspect bearing condition",
            "Check lubrication levels"
        ]
    else:
        rul_days = random.randint(7, 30)
        status = "poor"
        recommendations = [
            "⚠️ Immediate inspection required",
            "Prepare replacement parts",
            "Consider temporary load reduction"
        ]
    
    return {
        "device": device,
        "analysis_timestamp": datetime.now().isoformat(),
        "health_status": status,
        "degradation_score": round(degradation_score, 1),
        "estimated_rul_days": rul_days,
        "current_readings": {
            "temperature": temperature,
            "vibration": vibration,
        },
        "recommendations": recommendations
    }


@server.tool("get_energy_report")
async def get_energy_report():
    """
    Generate an energy consumption report for the factory.
    Includes current usage, trends, and efficiency recommendations.
    """
    current_kwh = simulator.read("energy_consumption")
    production = simulator.read("production_count")
    
    # Energy per unit produced
    energy_per_unit = current_kwh / production if production > 0 else 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "current_consumption_kwh": current_kwh,
        "production_count": int(production),
        "energy_per_unit": round(energy_per_unit, 4),
        "efficiency_rating": "A" if energy_per_unit < 0.1 else "B" if energy_per_unit < 0.15 else "C",
        "comparison": {
            "vs_yesterday": f"{random.uniform(-5, 5):.1f}%",
            "vs_last_week": f"{random.uniform(-10, 10):.1f}%",
            "vs_last_month": f"{random.uniform(-15, 15):.1f}%",
        },
        "recommendations": [
            "Optimize conveyor start/stop sequences",
            "Consider off-peak operation for batch processes",
        ]
    }


@server.tool("control_device")
async def control_device(device: str, action: str, value: float = None):
    """
    Send a control command to a device.
    
    Args:
        device: Target device name
        action: Control action (start, stop, set_speed, set_temperature)
        value: Optional value for actions that require it
        
    ⚠️ This is a simulation - no real device control is performed.
    """
    allowed_devices = ["pump_station", "conveyor_line"]
    allowed_actions = ["start", "stop", "set_speed", "set_temperature"]
    
    if device not in allowed_devices:
        return {"success": False, "error": f"Unknown device: {device}"}
    
    if action not in allowed_actions:
        return {"success": False, "error": f"Unknown action: {action}"}
    
    # Simulate control action
    return {
        "success": True,
        "device": device,
        "action": action,
        "value": value,
        "timestamp": datetime.now().isoformat(),
        "message": f"[SIMULATION] Command '{action}' sent to {device}",
        "note": "In production, this would control the actual device via Modbus/OPC UA"
    }


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("🏭 Smart Factory Dashboard")
    print("=" * 50)
    print()
    print("Starting Industrial MCP server with multi-device support...")
    print()
    print("Available tools for AI interaction:")
    print("  • get_factory_overview  - Full factory status")
    print("  • check_alerts          - Current warnings/alerts")
    print("  • predict_maintenance   - Predictive analytics")
    print("  • get_energy_report     - Energy consumption")
    print("  • control_device        - Device control (simulated)")
    print()
    print("Access points:")
    print("  📡 MCP Endpoint: http://localhost:8080")
    print("  📚 API Docs:     http://localhost:8080/docs")
    print("  🔧 Tools List:   http://localhost:8080/mcp/tools")
    print()
    
    server.run()
