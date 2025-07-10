# Async Serial Communication Script

A Python script for connecting to serial devices using asyncio with JSON configuration support.

## Features

- ✅ Asynchronous serial communication using `asyncio`
- ✅ JSON-based configuration for easy setup
- ✅ Continuous listening mode for real-time data
- ✅ Interactive mode for manual command sending
- ✅ Automatic configuration validation
- ✅ Comprehensive logging
- ✅ Graceful shutdown handling
- ✅ Extensible design for custom applications

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. The script will automatically create a default configuration file on first run.

## Configuration

The script uses a JSON configuration file (`serial_config.json`) to define serial port settings:

```json
{
    "port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "timeout": 1.0,
    "xonxoff": false,
    "rtscts": false,
    "dsrdtr": false,
    "read_buffer_size": 1024,
    "write_timeout": 1.0
}
```

### Configuration Parameters

| Parameter | Description | Default | Valid Values |
|-----------|-------------|---------|--------------|
| `port` | Serial port device path | `/dev/ttyUSB0` | `/dev/ttyUSB0`, `/dev/ttyACM0`, `COM1`, etc. |
| `baudrate` | Communication speed | `9600` | `300`, `1200`, `9600`, `115200`, etc. |
| `bytesize` | Number of data bits | `8` | `5`, `6`, `7`, `8` |
| `parity` | Parity checking | `N` | `N` (None), `E` (Even), `O` (Odd) |
| `stopbits` | Number of stop bits | `1` | `1`, `1.5`, `2` |
| `timeout` | Read timeout in seconds | `1.0` | Any positive number |
| `xonxoff` | Software flow control | `false` | `true`, `false` |
| `rtscts` | Hardware RTS/CTS flow control | `false` | `true`, `false` |
| `dsrdtr` | Hardware DSR/DTR flow control | `false` | `true`, `false` |

## Usage

### Basic Usage (Continuous Listening)

```bash
python3 serial_client.py
```

This mode:
- Connects to the serial device
- Continuously listens for incoming data
- Sends a test message after connection
- Logs all received data

### Interactive Mode

```bash
python3 serial_client.py --interactive
```

This mode allows you to manually type commands to send to the device.

### Programmatic Usage

```python
import asyncio
from serial_client import AsyncSerialClient, SerialConfig

async def main():
    config = SerialConfig("serial_config.json")
    client = AsyncSerialClient(config)
    
    if await client.connect():
        # Send data
        await client.send_data("Hello Device!")
        
        # Read response
        response = await client.read_data()
        print(f"Received: {response}")
        
        await client.disconnect()

asyncio.run(main())
```

## Extending the Client

Create a custom client by inheriting from `AsyncSerialClient`:

```python
class MyCustomClient(AsyncSerialClient):
    async def process_received_data(self, data: str):
        # Custom data processing
        if data.startswith("TEMP:"):
            temperature = data.split(":")[1]
            print(f"Temperature: {temperature}°C")
```

See `example_usage.py` for more detailed examples.

## Common Serial Devices

### Arduino/ESP32
```json
{
    "port": "/dev/ttyUSB0",
    "baudrate": 115200
}
```

### GPS Modules
```json
{
    "port": "/dev/ttyACM0", 
    "baudrate": 9600
}
```

### Industrial Sensors
```json
{
    "port": "/dev/ttyRS485",
    "baudrate": 19200,
    "parity": "E"
}
```

## Troubleshooting

### Permission Denied
```bash
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Device Not Found
- Check if device is connected: `ls /dev/tty*`
- Verify the correct port in `serial_config.json`
- Check if another application is using the port

### Connection Timeouts
- Verify baudrate matches device settings
- Check hardware flow control settings
- Ensure proper cable connections

## Logging

The script provides detailed logging with timestamps:
- Connection status
- Data sent/received
- Error messages
- Configuration validation

Log level can be adjusted in the script by modifying the `logging.basicConfig()` call.

## Signal Handling

The script handles shutdown signals gracefully:
- `Ctrl+C` (SIGINT)
- `SIGTERM`
- Proper cleanup and disconnection

## Dependencies

- `pyserial-asyncio`: Async serial communication
- `pyserial`: Serial port access
- Standard library: `asyncio`, `json`, `logging`

## License

This script is provided as-is for educational and development purposes.
