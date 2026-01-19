"""
MQTT protocol adapter for IoT sensors and lightweight devices.

MQTT is a lightweight messaging protocol commonly used for IoT
sensors and edge devices in industrial environments.
"""

from typing import Any, Callable, Dict, List, Optional
import asyncio
import json

import structlog
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage

from industrial_mcp.adapters.base import BaseAdapter

logger = structlog.get_logger()


class MQTTAdapter(BaseAdapter):
    """
    MQTT adapter for IoT sensors and lightweight devices.
    
    This adapter allows subscribing to MQTT topics and publishing
    messages, making it ideal for IoT sensor data collection.
    
    Example:
        ```python
        adapter = MQTTAdapter(
            host="192.168.1.50",
            port=1883,
            device_name="sensors"
        )
        await adapter.connect()
        
        # Subscribe to sensor data
        await adapter.subscribe("factory/sensors/temperature")
        
        # Get latest value
        temp = adapter.get_value("factory/sensors/temperature")
        
        # Publish a command
        await adapter.publish("factory/actuators/valve", {"state": "open"})
        ```
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        device_name: str = "mqtt-device",
        client_id: str = None,
        username: str = None,
        password: str = None,
        use_tls: bool = False,
    ):
        super().__init__(host, port, device_name)
        self.client_id = client_id or f"industrial-mcp-{device_name}"
        self.username = username
        self.password = password
        self.use_tls = use_tls
        
        self._client: Optional[mqtt.Client] = None
        self._values: Dict[str, Any] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
    @property
    def protocol_name(self) -> str:
        return "mqtt"
    
    async def connect(self) -> bool:
        """Establish connection to the MQTT broker."""
        try:
            self._loop = asyncio.get_event_loop()
            self._client = mqtt.Client(client_id=self.client_id)
            
            # Configure callbacks
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect
            
            # Configure authentication
            if self.username and self.password:
                self._client.username_pw_set(self.username, self.password)
            
            # Configure TLS
            if self.use_tls:
                self._client.tls_set()
            
            # Connect (non-blocking)
            self._client.connect_async(self.host, self.port)
            self._client.loop_start()
            
            # Wait for connection
            await asyncio.sleep(1)
            
            if self._client.is_connected():
                self._connected = True
                logger.info("MQTT connected", host=self.host, port=self.port)
                return True
            else:
                logger.warning("MQTT connection pending", host=self.host)
                return False
                
        except Exception as e:
            logger.error("MQTT connection error", error=str(e))
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close connection to the MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("MQTT disconnected", host=self.host)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        if rc == 0:
            self._connected = True
            logger.info("MQTT connected callback")
        else:
            logger.error("MQTT connection failed", rc=rc)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker."""
        self._connected = False
        logger.info("MQTT disconnected callback", rc=rc)
    
    def _on_message(self, client, userdata, message: MQTTMessage):
        """Callback when message received."""
        topic = message.topic
        
        try:
            # Try to parse as JSON
            payload = json.loads(message.payload.decode())
        except:
            # Fall back to raw string
            payload = message.payload.decode()
        
        # Store latest value
        self._values[topic] = payload
        
        # Call registered callbacks
        if topic in self._callbacks:
            for callback in self._callbacks[topic]:
                if self._loop:
                    self._loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(callback(topic, payload))
                    )
    
    async def read(self, address: str) -> Any:
        """
        Read the latest value from a topic.
        
        Args:
            address: MQTT topic
            
        Returns:
            Latest value received on that topic
        """
        return self.get_value(address)
    
    async def write(self, address: str, value: Any) -> bool:
        """
        Publish a message to a topic.
        
        Args:
            address: MQTT topic
            value: Value to publish
            
        Returns:
            True if published successfully
        """
        return await self.publish(address, value)
    
    def get_value(self, topic: str) -> Optional[Any]:
        """
        Get the latest value received on a topic.
        
        Args:
            topic: MQTT topic
            
        Returns:
            Latest value or None if no value received yet
        """
        return self._values.get(topic)
    
    def get_all_values(self) -> Dict[str, Any]:
        """
        Get all stored topic values.
        
        Returns:
            Dictionary of topic -> latest value
        """
        return self._values.copy()
    
    async def subscribe(
        self, 
        topic: str, 
        callback: Callable = None,
        qos: int = 0
    ) -> bool:
        """
        Subscribe to an MQTT topic.
        
        Args:
            topic: MQTT topic (supports wildcards: +, #)
            callback: Optional async callback function(topic, payload)
            qos: Quality of Service level (0, 1, or 2)
            
        Returns:
            True if subscription successful
        """
        if not self._client or not self._connected:
            return False
            
        try:
            result, mid = self._client.subscribe(topic, qos)
            
            if callback:
                if topic not in self._callbacks:
                    self._callbacks[topic] = []
                self._callbacks[topic].append(callback)
            
            logger.info("MQTT subscribed", topic=topic)
            return result == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error("MQTT subscribe error", error=str(e))
            return False
    
    async def publish(
        self, 
        topic: str, 
        payload: Any, 
        qos: int = 0,
        retain: bool = False
    ) -> bool:
        """
        Publish a message to an MQTT topic.
        
        Args:
            topic: MQTT topic
            payload: Message payload (will be JSON-encoded if dict/list)
            qos: Quality of Service level
            retain: Whether to retain the message
            
        Returns:
            True if published successfully
        """
        if not self._client or not self._connected:
            return False
            
        try:
            # Encode payload
            if isinstance(payload, (dict, list)):
                message = json.dumps(payload)
            else:
                message = str(payload)
            
            result = self._client.publish(topic, message, qos, retain)
            
            logger.info("MQTT published", topic=topic)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error("MQTT publish error", error=str(e))
            return False
