"""
AI Chat Interface Example

This example demonstrates how to connect an AI chatbot (using Ollama)
to the Industrial MCP server, enabling natural language interaction
with factory equipment.

This is the "conversational machine interface" vision in action:
Instead of complex dashboards, operators can simply ask:
  "How's the pump doing?"
  "Should we schedule maintenance?"
  "What's our energy efficiency today?"

Requirements:
    pip install industrial-mcp[llm]
    ollama pull llama3.2  # or any other model
    
Run with:
    1. First start the MCP server: industrial-mcp serve --demo
    2. Then run: python examples/ai_chat_interface.py
"""

import json
import httpx
from typing import Optional


# =============================================================================
# Configuration
# =============================================================================

MCP_SERVER_URL = "http://localhost:8080"
OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.2"  # or "mistral", "qwen2.5", etc.


# =============================================================================
# MCP Client
# =============================================================================

class MCPClient:
    """Simple client for interacting with an MCP server."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30)
    
    def list_tools(self) -> list:
        """Get all available tools from the server."""
        response = self.client.get(f"{self.base_url}/mcp/tools")
        response.raise_for_status()
        return response.json()
    
    def call_tool(self, name: str, args: dict = None) -> dict:
        """Call a tool by name with optional arguments."""
        response = self.client.post(
            f"{self.base_url}/mcp/tools/{name}/call",
            json=args or {}
        )
        response.raise_for_status()
        return response.json()


# =============================================================================
# AI Integration
# =============================================================================

def create_system_prompt(tools: list) -> str:
    """Create a system prompt that tells the AI about available tools."""
    
    tool_descriptions = []
    for tool in tools:
        tool_descriptions.append(
            f"- **{tool['name']}**: {tool['description']}"
        )
    
    return f"""You are a helpful industrial AI assistant for a smart factory.
You have access to real-time data from factory equipment through these tools:

{chr(10).join(tool_descriptions)}

When the user asks about:
- Factory status → use get_factory_overview
- Problems or alerts → use check_alerts
- Equipment health or maintenance → use predict_maintenance
- Energy or efficiency → use get_energy_report
- Controlling devices → use control_device

Always respond conversationally and explain data in simple terms.
If you use a tool, summarize the results clearly for the operator.

IMPORTANT: When you need to use a tool, respond with:
TOOL: tool_name
ARGS: {{"param": "value"}}

Then wait for the result before continuing.
"""


def chat_with_ollama(
    message: str,
    system_prompt: str,
    conversation_history: list,
    model: str = MODEL
) -> str:
    """Send a message to Ollama and get a response."""
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": message})
    
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except httpx.ConnectError:
        return "Error: Cannot connect to Ollama. Is it running? (ollama serve)"
    except Exception as e:
        return f"Error: {e}"


def parse_tool_call(response: str) -> Optional[tuple]:
    """Parse a tool call from the AI's response."""
    
    lines = response.strip().split("\n")
    tool_name = None
    tool_args = {}
    
    for i, line in enumerate(lines):
        if line.startswith("TOOL:"):
            tool_name = line.replace("TOOL:", "").strip()
        elif line.startswith("ARGS:"):
            try:
                args_str = line.replace("ARGS:", "").strip()
                tool_args = json.loads(args_str)
            except json.JSONDecodeError:
                tool_args = {}
    
    if tool_name:
        return (tool_name, tool_args)
    return None


# =============================================================================
# Chat Interface
# =============================================================================

def main():
    """Run the interactive chat interface."""
    
    print("🤖 Industrial AI Chat Interface")
    print("=" * 50)
    print()
    
    # Connect to MCP server
    try:
        mcp = MCPClient(MCP_SERVER_URL)
        tools = mcp.list_tools()
        print(f"✅ Connected to MCP server at {MCP_SERVER_URL}")
        print(f"   Found {len(tools)} tools available")
    except httpx.ConnectError:
        print(f"❌ Cannot connect to MCP server at {MCP_SERVER_URL}")
        print("   Start the server first: industrial-mcp serve --demo")
        return
    
    print()
    print("Enter your questions about the factory.")
    print("Type 'quit' or 'exit' to end the session.")
    print("=" * 50)
    print()
    
    system_prompt = create_system_prompt(tools)
    conversation_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 Goodbye!")
            break
        
        # Get AI response
        print("AI: ", end="", flush=True)
        response = chat_with_ollama(
            user_input,
            system_prompt,
            conversation_history
        )
        
        # Check if AI wants to use a tool
        tool_call = parse_tool_call(response)
        
        if tool_call:
            tool_name, tool_args = tool_call
            print(f"[Using tool: {tool_name}...]")
            
            try:
                tool_result = mcp.call_tool(tool_name, tool_args)
                
                # Send result back to AI for interpretation
                result_message = f"Tool result for {tool_name}:\n{json.dumps(tool_result, indent=2)}"
                
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})
                conversation_history.append({"role": "user", "content": result_message})
                
                # Get AI's interpretation of the result
                interpretation = chat_with_ollama(
                    "Based on this tool result, please provide a clear summary for the operator.",
                    system_prompt,
                    conversation_history
                )
                
                print(interpretation)
                conversation_history.append({"role": "assistant", "content": interpretation})
                
            except Exception as e:
                print(f"Tool error: {e}")
                
        else:
            print(response)
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})
        
        print()


# =============================================================================
# Example Conversation
# =============================================================================

EXAMPLE_CONVERSATION = """
Example conversation:

You: How's the factory doing today?
AI: [Using tool: get_factory_overview...]
    The factory is running smoothly! Here's a quick summary:
    
    🔧 Pump Station: Running at 55°C, pressure 5.5 bar, flow rate 120 L/min
    🏭 Conveyor Line: Speed 1.5 m/s, motor current 12A
    📊 Production: 15,420 units today with 98.5% quality score
    ⚡ Energy: 1,250 kWh consumed
    
    All systems are operating within normal parameters.

You: Should we schedule maintenance for the pump soon?
AI: [Using tool: predict_maintenance...]
    Based on the current readings, the pump is in good condition!
    
    Health Status: Good
    Estimated Remaining Life: ~120 days
    
    Recommendations:
    - Schedule routine inspection in 30 days
    - Continue monitoring vibration trends
    
    No urgent maintenance is needed right now.

You: What's our energy efficiency like?
AI: [Using tool: get_energy_report...]
    Great news! Your energy efficiency rating is A+ today.
    
    - Current consumption: 1,250 kWh
    - Energy per unit: 0.081 kWh (very efficient!)
    - 3.5% lower than yesterday
    
    Tip: Consider optimizing conveyor start/stop sequences 
    during shift changes for even better efficiency.
"""


if __name__ == "__main__":
    print(EXAMPLE_CONVERSATION)
    print()
    main()
