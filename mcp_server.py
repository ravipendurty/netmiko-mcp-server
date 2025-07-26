#!/usr/bin/env python3
"""
MCP Server for NetMiko - Network Device Management
Provides MCP protocol interface for managing network devices via SSH using NetMiko
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import yaml


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeviceConfig:
    """Configuration for a network device"""
    host: str
    device_type: str
    username: str
    password: str
    port: int = 22
    secret: Optional[str] = None
    timeout: int = 30
    session_timeout: int = 60


class NetMikoMCPServer:
    """MCP Server implementation for NetMiko network device management"""
    
    def __init__(self):
        self.server = Server("netmiko-mcp-server")
        self.connections: Dict[str, ConnectHandler] = {}
        self.device_configs: Dict[str, DeviceConfig] = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List available network devices as resources"""
            resources = []
            for device_id, config in self.device_configs.items():
                resources.append(
                    types.Resource(
                        uri=f"device://{device_id}",
                        name=f"Network Device: {config.host}",
                        description=f"Network device {config.host} ({config.device_type})",
                        mimeType="application/json"
                    )
                )
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: types.AnyUrl) -> str:
            """Read device information"""
            if not str(uri).startswith("device://"):
                raise ValueError(f"Unknown resource URI: {uri}")
            
            device_id = str(uri).replace("device://", "")
            if device_id not in self.device_configs:
                raise ValueError(f"Device not found: {device_id}")
            
            config = self.device_configs[device_id]
            device_info = {
                "device_id": device_id,
                "host": config.host,
                "device_type": config.device_type,
                "port": config.port,
                "timeout": config.timeout,
                "connected": device_id in self.connections
            }
            
            return json.dumps(device_info, indent=2)
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools for network device management"""
            return [
                types.Tool(
                    name="connect_device",
                    description="Connect to a network device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {"type": "string", "description": "Unique device identifier"},
                            "host": {"type": "string", "description": "Device IP address or hostname"},
                            "device_type": {"type": "string", "description": "Device type (cisco_ios, cisco_nxos, etc.)"},
                            "username": {"type": "string", "description": "SSH username"},
                            "password": {"type": "string", "description": "SSH password"},
                            "port": {"type": "integer", "description": "SSH port (default: 22)", "default": 22},
                            "secret": {"type": "string", "description": "Enable secret (optional)"},
                            "timeout": {"type": "integer", "description": "Connection timeout (default: 30)", "default": 30}
                        },
                        "required": ["device_id", "host", "device_type", "username", "password"]
                    }
                ),
                types.Tool(
                    name="disconnect_device",
                    description="Disconnect from a network device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {"type": "string", "description": "Device identifier to disconnect"}
                        },
                        "required": ["device_id"]
                    }
                ),
                types.Tool(
                    name="send_command",
                    description="Send a command to a connected network device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {"type": "string", "description": "Device identifier"},
                            "command": {"type": "string", "description": "Command to execute"},
                            "use_textfsm": {"type": "boolean", "description": "Parse output with TextFSM", "default": False},
                            "strip_prompt": {"type": "boolean", "description": "Strip device prompt from output", "default": True},
                            "strip_command": {"type": "boolean", "description": "Strip command from output", "default": True}
                        },
                        "required": ["device_id", "command"]
                    }
                ),
                types.Tool(
                    name="send_config_commands",
                    description="Send configuration commands to a network device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {"type": "string", "description": "Device identifier"},
                            "commands": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of configuration commands"
                            },
                            "exit_config_mode": {"type": "boolean", "description": "Exit config mode after commands", "default": True}
                        },
                        "required": ["device_id", "commands"]
                    }
                ),
                types.Tool(
                    name="get_device_info",
                    description="Get basic device information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {"type": "string", "description": "Device identifier"}
                        },
                        "required": ["device_id"]
                    }
                ),
                types.Tool(
                    name="list_connected_devices",
                    description="List all currently connected devices",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "connect_device":
                    return await self._connect_device(**arguments)
                elif name == "disconnect_device":
                    return await self._disconnect_device(**arguments)
                elif name == "send_command":
                    return await self._send_command(**arguments)
                elif name == "send_config_commands":
                    return await self._send_config_commands(**arguments)
                elif name == "get_device_info":
                    return await self._get_device_info(**arguments)
                elif name == "list_connected_devices":
                    return await self._list_connected_devices()
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _connect_device(self, device_id: str, host: str, device_type: str, 
                            username: str, password: str, port: int = 22, 
                            secret: Optional[str] = None, timeout: int = 30) -> list[types.TextContent]:
        """Connect to a network device"""
        try:
            # Store device configuration
            config = DeviceConfig(
                host=host,
                device_type=device_type,
                username=username,
                password=password,
                port=port,
                secret=secret,
                timeout=timeout
            )
            self.device_configs[device_id] = config
            
            # Create connection parameters
            device_params = {
                'device_type': device_type,
                'host': host,
                'username': username,
                'password': password,
                'port': port,
                'timeout': timeout,
            }
            
            if secret:
                device_params['secret'] = secret
            
            # Establish connection
            connection = ConnectHandler(**device_params)
            self.connections[device_id] = connection
            
            # Get device prompt for verification
            prompt = connection.find_prompt()
            
            return [types.TextContent(
                type="text",
                text=f"Successfully connected to device {device_id} ({host}). Device prompt: {prompt}"
            )]
            
        except NetmikoAuthenticationException as e:
            return [types.TextContent(
                type="text",
                text=f"Authentication failed for device {device_id}: {str(e)}"
            )]
        except NetmikoTimeoutException as e:
            return [types.TextContent(
                type="text",
                text=f"Connection timeout for device {device_id}: {str(e)}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Failed to connect to device {device_id}: {str(e)}"
            )]
    
    async def _disconnect_device(self, device_id: str) -> list[types.TextContent]:
        """Disconnect from a network device"""
        if device_id not in self.connections:
            return [types.TextContent(
                type="text",
                text=f"Device {device_id} is not connected"
            )]
        
        try:
            connection = self.connections[device_id]
            connection.disconnect()
            del self.connections[device_id]
            
            return [types.TextContent(
                type="text",
                text=f"Successfully disconnected from device {device_id}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error disconnecting from device {device_id}: {str(e)}"
            )]
    
    async def _send_command(self, device_id: str, command: str, 
                          use_textfsm: bool = False, strip_prompt: bool = True,
                          strip_command: bool = True) -> list[types.TextContent]:
        """Send a command to a network device"""
        if device_id not in self.connections:
            return [types.TextContent(
                type="text",
                text=f"Device {device_id} is not connected. Please connect first."
            )]
        
        try:
            connection = self.connections[device_id]
            output = connection.send_command(
                command,
                use_textfsm=use_textfsm,
                strip_prompt=strip_prompt,
                strip_command=strip_command
            )
            
            if use_textfsm and isinstance(output, list):
                # Format structured output
                formatted_output = json.dumps(output, indent=2)
            else:
                formatted_output = str(output)
            
            return [types.TextContent(
                type="text",
                text=f"Command: {command}\n\nOutput:\n{formatted_output}"
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error executing command on device {device_id}: {str(e)}"
            )]
    
    async def _send_config_commands(self, device_id: str, commands: List[str],
                                  exit_config_mode: bool = True) -> list[types.TextContent]:
        """Send configuration commands to a network device"""
        if device_id not in self.connections:
            return [types.TextContent(
                type="text",
                text=f"Device {device_id} is not connected. Please connect first."
            )]
        
        try:
            connection = self.connections[device_id]
            output = connection.send_config_set(
                commands,
                exit_config_mode=exit_config_mode
            )
            
            return [types.TextContent(
                type="text",
                text=f"Configuration commands executed:\n{chr(10).join(commands)}\n\nOutput:\n{output}"
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error executing config commands on device {device_id}: {str(e)}"
            )]
    
    async def _get_device_info(self, device_id: str) -> list[types.TextContent]:
        """Get device information"""
        if device_id not in self.connections:
            return [types.TextContent(
                type="text",
                text=f"Device {device_id} is not connected. Please connect first."
            )]
        
        try:
            connection = self.connections[device_id]
            config = self.device_configs[device_id]
            
            # Get basic device info
            prompt = connection.find_prompt()
            
            device_info = {
                "device_id": device_id,
                "host": config.host,
                "device_type": config.device_type,
                "port": config.port,
                "prompt": prompt,
                "connected": True,
                "session_timeout": config.session_timeout
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(device_info, indent=2)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting device info for {device_id}: {str(e)}"
            )]
    
    async def _list_connected_devices(self) -> list[types.TextContent]:
        """List all connected devices"""
        if not self.connections:
            return [types.TextContent(
                type="text",
                text="No devices currently connected"
            )]
        
        connected_devices = []
        for device_id, connection in self.connections.items():
            config = self.device_configs.get(device_id)
            if config:
                connected_devices.append({
                    "device_id": device_id,
                    "host": config.host,
                    "device_type": config.device_type,
                    "prompt": connection.find_prompt()
                })
        
        return [types.TextContent(
            type="text",
            text=json.dumps(connected_devices, indent=2)
        )]
    
    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="netmiko-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point"""
    server = NetMikoMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
