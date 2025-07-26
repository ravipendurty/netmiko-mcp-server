#!/usr/bin/env python3
"""
CLI interface for NetMiko MCP Server
Provides command-line utilities for server management and testing
"""

import click
import asyncio
import json
import yaml
from pathlib import Path
from typing import Dict, Any

from mcp_server import NetMikoMCPServer, DeviceConfig


@click.group()
def cli():
    """NetMiko MCP Server CLI"""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
def start(config):
    """Start the MCP server"""
    click.echo("Starting NetMiko MCP Server...")
    
    server = NetMikoMCPServer()
    
    # Load configuration if provided
    if config:
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
            
        # Pre-configure devices from config file
        if 'devices' in config_data:
            for device_id, device_config in config_data['devices'].items():
                server.device_configs[device_id] = DeviceConfig(**device_config)
                click.echo(f"Loaded device configuration: {device_id}")
    
    # Run the server
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        click.echo("\nServer stopped by user")
    except Exception as e:
        click.echo(f"Server error: {e}")


@cli.command()
@click.option('--host', '-h', required=True, help='Device hostname or IP')
@click.option('--device-type', '-t', required=True, help='Device type (cisco_ios, etc.)')
@click.option('--username', '-u', required=True, help='SSH username')
@click.option('--password', '-p', required=True, help='SSH password')
@click.option('--port', default=22, help='SSH port')
@click.option('--timeout', default=30, help='Connection timeout')
def test_connection(host, device_type, username, password, port, timeout):
    """Test connection to a network device"""
    click.echo(f"Testing connection to {host}...")
    
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
    
    device_params = {
        'device_type': device_type,
        'host': host,
        'username': username,
        'password': password,
        'port': port,
        'timeout': timeout,
    }
    
    try:
        connection = ConnectHandler(**device_params)
        prompt = connection.find_prompt()
        click.echo(f"✓ Connection successful! Device prompt: {prompt}")
        
        # Test a basic command
        output = connection.send_command("show version", strip_prompt=True, strip_command=True)
        click.echo(f"✓ Command execution successful")
        click.echo(f"Sample output (first 200 chars): {output[:200]}...")
        
        connection.disconnect()
        click.echo("✓ Disconnection successful")
        
    except NetmikoAuthenticationException:
        click.echo("✗ Authentication failed - check username/password")
    except NetmikoTimeoutException:
        click.echo("✗ Connection timeout - check host/port")
    except Exception as e:
        click.echo(f"✗ Connection failed: {e}")


@cli.command()
def list_device_types():
    """List supported device types"""
    device_types = [
        "cisco_ios", "cisco_nxos", "cisco_xr", "cisco_asa",
        "arista_eos", "juniper_junos", "hp_procurve", "dell_force10",
        "paloalto_panos", "fortinet", "checkpoint_gaia", "linux"
    ]
    
    click.echo("Supported device types:")
    for device_type in device_types:
        click.echo(f"  - {device_type}")


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def generate_config(output):
    """Generate a sample configuration file"""
    config = {
        'server': {
            'name': 'netmiko-mcp-server',
            'version': '1.0.0',
            'log_level': 'INFO'
        },
        'devices': {
            'example_router': {
                'host': '192.168.1.1',
                'device_type': 'cisco_ios',
                'username': 'admin',
                'password': 'password',
                'port': 22,
                'timeout': 30,
                'secret': 'enable_secret'
            },
            'example_switch': {
                'host': '192.168.1.10',
                'device_type': 'cisco_ios',
                'username': 'admin',
                'password': 'password',
                'port': 22,
                'timeout': 30
            }
        }
    }
    
    config_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    if output:
        with open(output, 'w') as f:
            f.write(config_yaml)
        click.echo(f"Configuration written to {output}")
    else:
        click.echo("Sample configuration:")
        click.echo(config_yaml)


if __name__ == '__main__':
    cli()
