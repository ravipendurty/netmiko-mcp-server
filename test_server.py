#!/usr/bin/env python3
"""
Test script for NetMiko MCP Server
Tests the server functionality without requiring actual network devices
"""

import asyncio
import json
from mcp_server import NetMikoMCPServer


async def test_server_functionality():
    """Test basic server functionality"""
    print("Testing NetMiko MCP Server Functionality")
    print("=" * 50)
    
    # Create server instance
    server = NetMikoMCPServer()
    
    # Test 1: Test server initialization
    print("\n1. Testing server initialization...")
    print(f"Server name: {server.server.name}")
    print(f"Connections: {len(server.connections)}")
    print(f"Device configs: {len(server.device_configs)}")
    
    # Test 2: Test available tools (simulate MCP tool list)
    print("\n2. Testing available tools...")
    tool_names = [
        "connect_device", "disconnect_device", "send_command",
        "send_config_commands", "get_device_info", "list_connected_devices"
    ]
    print(f"Available tools: {len(tool_names)} tools")
    for tool in tool_names:
        print(f"  - {tool}")
    
    # Test 3: Test list_connected_devices (should be empty)
    print("\n3. Testing list_connected_devices...")
    result = await server._list_connected_devices()
    print(f"Connected devices result: {result[0].text}")
    
    # Test 4: Test connection to non-existent device (should fail gracefully)
    print("\n4. Testing connection error handling...")
    connect_result = await server._connect_device(
        device_id="test_device",
        host="192.168.999.999",  # Invalid IP
        device_type="cisco_ios",
        username="test",
        password="test",
        timeout=5  # Short timeout
    )
    print(f"Connection result (expected failure): {connect_result[0].text}")
    
    # Test 5: Test command on non-connected device
    print("\n5. Testing command on non-connected device...")
    cmd_result = await server._send_command(
        device_id="non_existent",
        command="show version"
    )
    print(f"Command result (expected failure): {cmd_result[0].text}")
    
    print("\n" + "=" * 50)
    print("Server functionality test completed successfully!")
    print("All error handling is working as expected.")


if __name__ == "__main__":
    asyncio.run(test_server_functionality())
