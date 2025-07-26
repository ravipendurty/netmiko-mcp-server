# NetMiko MCP Server

A Model Context Protocol (MCP) server that provides network device management capabilities using NetMiko. This server allows MCP clients to connect to and manage network devices via SSH.

## Features

- **Device Connection Management**: Connect/disconnect to network devices
- **Command Execution**: Send show commands and configuration commands
- **Multiple Device Support**: Manage multiple devices simultaneously
- **TextFSM Integration**: Parse command outputs into structured data
- **Security**: Secure SSH connections with authentication
- **Device Types**: Support for Cisco, Arista, Juniper, HP, Dell, and more

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
# Start with default configuration
python mcp_server.py

# Start with custom configuration
python cli.py start --config config.yaml
```

### CLI Tools

The server includes a CLI interface for testing and management:

```bash
# Test connection to a device
python cli.py test-connection -h 192.168.1.1 -t cisco_ios -u admin -p password

# List supported device types
python cli.py list-device-types

# Generate sample configuration
python cli.py generate-config -o my_config.yaml
```

## MCP Tools

The server provides the following MCP tools:

### connect_device
Connect to a network device.

**Parameters:**
- `device_id` (string): Unique identifier for the device
- `host` (string): IP address or hostname
- `device_type` (string): Device type (cisco_ios, cisco_nxos, etc.)
- `username` (string): SSH username
- `password` (string): SSH password
- `port` (integer, optional): SSH port (default: 22)
- `secret` (string, optional): Enable secret
- `timeout` (integer, optional): Connection timeout (default: 30)

### disconnect_device
Disconnect from a network device.

**Parameters:**
- `device_id` (string): Device identifier to disconnect

### send_command
Send a show command to a connected device.

**Parameters:**
- `device_id` (string): Device identifier
- `command` (string): Command to execute
- `use_textfsm` (boolean, optional): Parse output with TextFSM
- `strip_prompt` (boolean, optional): Strip device prompt from output
- `strip_command` (boolean, optional): Strip command from output

### send_config_commands
Send configuration commands to a device.

**Parameters:**
- `device_id` (string): Device identifier
- `commands` (array): List of configuration commands
- `exit_config_mode` (boolean, optional): Exit config mode after commands

### get_device_info
Get information about a connected device.

**Parameters:**
- `device_id` (string): Device identifier

### list_connected_devices
List all currently connected devices.

## Configuration

Create a `config.yaml` file to pre-configure devices:

```yaml
server:
  name: "netmiko-mcp-server"
  version: "1.0.0"
  log_level: "INFO"

devices:
  router1:
    host: "192.168.1.1"
    device_type: "cisco_ios"
    username: "admin"
    password: "password"
    port: 22
    timeout: 30
    secret: "enable_secret"
```

## Supported Device Types

- cisco_ios
- cisco_nxos
- cisco_xr
- cisco_asa
- arista_eos
- juniper_junos
- hp_procurve
- dell_force10
- paloalto_panos
- fortinet
- checkpoint_gaia
- linux

## Example Usage

1. **Connect to a device:**
```json
{
  "tool": "connect_device",
  "arguments": {
    "device_id": "router1",
    "host": "192.168.1.1",
    "device_type": "cisco_ios",
    "username": "admin",
    "password": "password"
  }
}
```

2. **Send a show command:**
```json
{
  "tool": "send_command",
  "arguments": {
    "device_id": "router1",
    "command": "show ip interface brief",
    "use_textfsm": true
  }
}
```

3. **Configure the device:**
```json
{
  "tool": "send_config_commands",
  "arguments": {
    "device_id": "router1",
    "commands": [
      "interface GigabitEthernet0/1",
      "description Connected to Switch1",
      "no shutdown"
    ]
  }
}
```

## Security Considerations

- Store credentials securely (consider using environment variables)
- Use SSH keys when possible
- Implement proper access controls
- Monitor and log all device interactions
- Use secure network connections

## Error Handling

The server handles common network device errors:
- Authentication failures
- Connection timeouts
- Command execution errors
- Device disconnections

## Development

To extend the server:

1. Add new tools in the `_setup_handlers()` method
2. Implement corresponding handler methods
3. Update the tool list in `handle_list_tools()`
4. Test with various device types

## License

This project is open source. Please check the license file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
- Check the NetMiko documentation
- Review MCP protocol specifications
- Create an issue in the repository
