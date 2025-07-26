#!/usr/bin/env python3
"""
Example usage of NetMiko MCP Server
Demonstrates how to interact with the MCP server programmatically
"""

import asyncio
import json
from mcp_server import NetMikoMCPServer


async def example_usage():
    """Example demonstrating MCP server usage"""
    
    # Create server instance
    server = NetMikoMCPServer()
    
    print("NetMiko MCP Server Example Usage")
    print("=" * 40)
    
    # Example 1: Connect to a device
    print("\n1. Connecting to device...")
    connect_result = await server._connect_device(
        device_id="test_router",
        host="192.168.1.1",  # Replace with actual device IP
        device_type="cisco_ios",
        username="admin",     # Replace with actual credentials
        password="password"
    )
    print(f"Connect result: {connect_result[0].text}")
    
    # Example 2: Send a show command
    print("\n2. Sending show command...")
    command_result = await server._send_command(
        device_id="test_router",
        command="show version"
    )
    print(f"Command result: {command_result[0].text[:200]}...")
    
    # Example 3: Send structured command with TextFSM
    print("\n3. Sending structured command...")
    structured_result = await server._send_command(
        device_id="test_router",
        command="show ip interface brief",
        use_textfsm=True
    )
    print(f"Structured result: {structured_result[0].text[:200]}...")
    
    # Example 4: Send configuration commands
    print("\n4. Sending configuration commands...")
    config_commands = [
        "interface loopback 100",
        "description Test loopback created by MCP",
        "ip address 10.100.100.1 255.255.255.255"
    ]
    config_result = await server._send_config_commands(
        device_id="test_router",
        commands=config_commands
    )
    print(f"Config result: {config_result[0].text}")
    
    # Example 5: Get device info
    print("\n5. Getting device information...")
    info_result = await server._get_device_info(device_id="test_router")
    print(f"Device info: {info_result[0].text}")
    
    # Example 6: List connected devices
    print("\n6. Listing connected devices...")
    list_result = await server._list_connected_devices()
    print(f"Connected devices: {list_result[0].text}")
    
    # Example 7: Disconnect from device
    print("\n7. Disconnecting from device...")
    disconnect_result = await server._disconnect_device(device_id="test_router")
    print(f"Disconnect result: {disconnect_result[0].text}")


if __name__ == "__main__":
    print("Note: This example requires actual network devices to connect to.")
    print("Please update the connection parameters before running.")
    
    # Uncomment the line below to run the example
    # asyncio.run(example_usage())
