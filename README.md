

<h1 align="center">🏭 Industrial MCP</h1>

<p align="center">
  <strong>The Open-Source Bridge Between AI and Industrial Equipment</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#supported-protocols">Protocols</a> •
  <a href="#documentation">Docs</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"/>
  <img src="https://img.shields.io/badge/python-3.10+-green.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/MCP-compatible-orange.svg" alt="MCP"/>
  <img src="https://img.shields.io/badge/edge--ready-yes-brightgreen.svg" alt="Edge Ready"/>
</p>

---

## 🌟 What is Industrial MCP?

**Industrial MCP** is an open-source project that implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) for industrial environments. It allows any AI model (Claude, GPT, Mistral, Llama, etc.) to **read data from** and **control** industrial equipment through a standardized interface.

> **Think of it as USB-C for Industrial AI** — one universal connector for all your machines.

### The Problem We Solve

```
❌ Traditional Approach:
   AI Model ←→ Custom API 1 ←→ Machine 1 (Modbus)
   AI Model ←→ Custom API 2 ←→ Machine 2 (OPC UA)  
   AI Model ←→ Custom API 3 ←→ Machine 3 (MQTT)
   = N×M integration nightmare 😱

✅ With Industrial MCP:
   AI Model ←→ MCP Protocol ←→ Industrial MCP Server ←→ Any Machine
   = One standard interface for everything 🎉
```

---

## ✨ Features

| Feature | Description |
|:--------|:------------|
| 🔌 **Multi-Protocol Support** | Modbus TCP/RTU, OPC UA, MQTT, S7 (Siemens) |
| 🤖 **AI-Ready** | Works with Claude, ChatGPT, Mistral, local LLMs |
| 📍 **Edge-First** | Runs on Raspberry Pi, Jetson, any Linux device |
| 🔒 **Data Sovereignty** | All processing on-premise, no cloud required |
| 🇪🇺 **GDPR Compliant** | Data never leaves your factory |
| 💬 **Natural Language** | Talk to your machines in plain language |
| 📊 **Built-in Monitoring** | Real-time dashboards and alerts |
| 🔧 **Extensible** | Add custom protocols with simple Python plugins |

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/industrial-mcp.git
cd industrial-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Basic Usage

```python
from industrial_mcp import MCPServer, ModbusAdapter

# Create MCP server
server = MCPServer(name="my-factory")

# Connect to a Modbus device (e.g., a pump)
pump = ModbusAdapter(
    host="192.168.1.100",
    port=502,
    device_name="pump-01"
)

# Register the device
server.register_device(pump)

# Define tools that AI can use
@server.tool("get_pump_status")
async def get_pump_status():
    """Get the current status of the main pump"""
    temp = await pump.read_register(address=100)
    vibration = await pump.read_register(address=101)
    return {
        "temperature": temp,
        "vibration": vibration,
        "status": "normal" if vibration < 50 else "warning"
    }

# Start the MCP server
server.run(host="0.0.0.0", port=8080)
```

### Connect with Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "industrial": {
      "command": "python",
      "args": ["-m", "industrial_mcp", "--config", "config.yaml"]
    }
  }
}
```

Now you can ask Claude:
> *"What's the temperature of pump-01?"*  
> *"Is the vibration level normal?"*  
> *"Show me the status of all connected devices."*

---

## 📡 Supported Protocols

| Protocol | Status | Use Case |
|:---------|:-------|:---------|
| **Modbus TCP** | ✅ Stable | PLCs, sensors, meters |
| **Modbus RTU** | ✅ Stable | Serial devices, RS-485 |
| **OPC UA** | ✅ Stable | Modern industrial systems |
| **MQTT** | ✅ Stable | IoT sensors, lightweight devices |
| **Siemens S7** | 🔄 Beta | Siemens PLCs (S7-300/400/1200/1500) |
| **BACnet** | 📋 Planned | Building automation |
| **EtherNet/IP** | 📋 Planned | Allen-Bradley, Rockwell |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR FACTORY                             │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Machine 1│  │ Machine 2│  │ Machine 3│  │ Sensor N │    │
│  │ (Modbus) │  │ (OPC UA) │  │  (MQTT)  │  │ (Modbus) │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│       └─────────────┴──────┬──────┴─────────────┘           │
│                            │                                 │
│                   ┌────────▼────────┐                       │
│                   │  INDUSTRIAL MCP  │                       │
│                   │     SERVER       │  ← Runs on Edge      │
│                   │  ┌────────────┐  │                       │
│                   │  │  Adapters  │  │                       │
│                   │  │  ┌──────┐  │  │                       │
│                   │  │  │Modbus│  │  │                       │
│                   │  │  │OPC UA│  │  │                       │
│                   │  │  │ MQTT │  │  │                       │
│                   │  │  └──────┘  │  │                       │
│                   │  └────────────┘  │                       │
│                   │  ┌────────────┐  │                       │
│                   │  │ MCP Server │  │                       │
│                   │  └────────────┘  │                       │
│                   └────────┬────────┘                       │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │ MCP Protocol (JSON-RPC)
                             ▼
                   ┌─────────────────┐
                   │    AI CLIENT    │
                   │  Claude / GPT   │
                   │  Local LLM      │
                   └─────────────────┘
```

---

## 💡 Use Cases

### 🔧 Predictive Maintenance
```python
@server.tool("analyze_vibration_pattern")
async def analyze_vibration():
    """Compare current vibration with historical failure patterns"""
    current = await pump.read_vibration()
    historical = await db.get_failure_patterns()
    similarity = calculate_similarity(current, historical)
    return {
        "similarity_to_failure": f"{similarity}%",
        "recommendation": "Schedule inspection" if similarity > 80 else "Normal"
    }
```

### 📊 Real-time Monitoring
```python
@server.tool("get_production_status")
async def get_production():
    """Get real-time production line status"""
    return {
        "units_produced": await plc.read("production_count"),
        "efficiency": await calculate_oee(),
        "downtime_minutes": await get_downtime()
    }
```

### 🚨 Anomaly Detection
```python
@server.tool("check_anomalies")
async def check_anomalies():
    """Detect anomalies across all connected devices"""
    anomalies = []
    for device in server.devices:
        if await device.is_anomalous():
            anomalies.append(device.name)
    return {"anomalies": anomalies, "count": len(anomalies)}
```

---

## 🖥️ Edge Deployment

### Raspberry Pi 4/5

```bash
# Install on Raspberry Pi
curl -sSL https://get.industrial-mcp.io | bash

# Or manually
pip install industrial-mcp[raspberry]
```

### NVIDIA Jetson

```bash
# Optimized for Jetson with local LLM support
pip install industrial-mcp[jetson]
```

### Docker

```bash
docker run -d \
  --name industrial-mcp \
  -p 8080:8080 \
  -v ./config.yaml:/app/config.yaml \
  industrialmcp/server:latest
```

---

## 📖 Documentation

| Document | Description |
|:---------|:------------|
| [Getting Started](docs/getting-started.md) | First steps with Industrial MCP |
| [Configuration](docs/configuration.md) | YAML configuration reference |
| [Adapters Guide](docs/adapters.md) | How to use protocol adapters |
| [Custom Adapters](docs/custom-adapters.md) | Write your own adapter |
| [Security](docs/security.md) | Authentication and encryption |
| [API Reference](docs/api.md) | Complete API documentation |

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone and install dev dependencies
git clone https://github.com/YOUR_USERNAME/industrial-mcp.git
cd industrial-mcp
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
```

### Roadmap

- [x] Modbus TCP/RTU adapter
- [x] OPC UA adapter  
- [x] MQTT adapter
- [x] Basic MCP server
- [ ] Siemens S7 adapter (in progress)
- [ ] Web dashboard
- [ ] Local LLM integration (Ollama)
- [ ] Anomaly detection ML models
- [ ] ATEX certification support

---

## 🌍 Community

- 💬 [Discord](https://discord.gg/industrial-mcp)
- 🐦 [Twitter](https://twitter.com/industrialmcp)
- 📧 [Mailing List](https://groups.google.com/g/industrial-mcp)

---

## 📜 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## 🏢 Enterprise Edition

Need more features for your enterprise?

| Feature | Open Source | Enterprise |
|:--------|:-----------:|:----------:|
| Core MCP Server | ✅ | ✅ |
| Modbus/OPC UA/MQTT | ✅ | ✅ |
| Community Support | ✅ | ✅ |
| Multi-site Management | ❌ | ✅ |
| Advanced Analytics Dashboard | ❌ | ✅ |
| Priority Support (SLA) | ❌ | ✅ |
| CE/ATEX Certification Kit | ❌ | ✅ |
| Custom Protocol Development | ❌ | ✅ |

📧 Contact: enterprise@industrial-mcp.io

---

<p align="center">
  Made with ❤️ in France 🇫🇷
</p>

<p align="center">
  <sub>Part of the <a href="https://lafrenchtech.com">La French Tech</a> ecosystem</sub>
</p>
