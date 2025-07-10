#!/usr/bin/env python3
"""
Asynchronous Serial Device Connection Script

This script connects to a serial device using asyncio and allows configuration
to be set from a JSON file.
"""

import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import serial_asyncio
    import serial
except ImportError:
    print("Error: pyserial-asyncio is required. Install with: pip install pyserial-asyncio")
    sys.exit(1)


class SerialConfig:
    """Configuration class for serial connection parameters."""
    
    def __init__(self, config_file: str = "serial_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            self._create_default_config()
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self._validate_config(config)
            return config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Error loading config file: {e}")
            raise
    
    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            "port": "/dev/ttyUSB0",
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "timeout": 1.0,
            "xonxoff": False,
            "rtscts": False,
            "dsrdtr": False,
            "read_buffer_size": 1024,
            "write_timeout": 1.0
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        print(f"Created default configuration file: {self.config_file}")
        print("Please edit the configuration file with your serial port settings.")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration parameters."""
        required_fields = ["port", "baudrate"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field in config: {field}")
        
        # Validate baudrate
        valid_baudrates = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        if config["baudrate"] not in valid_baudrates:
            logging.warning(f"Unusual baudrate: {config['baudrate']}. Common values: {valid_baudrates}")
        
        # Validate parity
        if "parity" in config:
            valid_parity = ["N", "E", "O", "M", "S"]
            if config["parity"] not in valid_parity:
                raise ValueError(f"Invalid parity: {config['parity']}. Valid values: {valid_parity}")
    
    def get_serial_params(self) -> Dict[str, Any]:
        """Get serial connection parameters."""
        # Map config keys to pyserial parameter names
        param_mapping = {
            "port": "port",
            "baudrate": "baudrate", 
            "bytesize": "bytesize",
            "parity": "parity",
            "stopbits": "stopbits",
            "timeout": "timeout",
            "xonxoff": "xonxoff",
            "rtscts": "rtscts",
            "dsrdtr": "dsrdtr"
        }
        
        params = {}
        for config_key, serial_key in param_mapping.items():
            if config_key in self.config:
                params[serial_key] = self.config[config_key]
        
        return params


class AsyncSerialClient:
    """Asynchronous serial client."""
    
    def __init__(self, config: SerialConfig):
        self.config = config
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """Connect to the serial device."""
        try:
            serial_params = self.config.get_serial_params()
            self.logger.info(f"Connecting to serial device: {serial_params['port']} at {serial_params['baudrate']} baud")
            
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=serial_params.pop('port'),
                **serial_params
            )
            
            self.logger.info("Successfully connected to serial device")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"Serial connection error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the serial device."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.logger.info("Disconnected from serial device")
    
    async def send_data(self, data: str) -> bool:
        """Send data to the serial device."""
        if not self.writer:
            self.logger.error("Not connected to serial device")
            return False
        
        try:
            # Ensure data ends with newline if not present
            if not data.endswith('\n'):
                data += '\n'
            
            self.writer.write(data.encode('utf-8'))
            await self.writer.drain()
            self.logger.info(f"Sent: {data.strip()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending data: {e}")
            return False
    
    async def read_data(self) -> Optional[str]:
        """Read data from the serial device."""
        if not self.reader:
            self.logger.error("Not connected to serial device")
            return None
        
        try:
            buffer_size = self.config.config.get("read_buffer_size", 1024)
            data = await self.reader.read(buffer_size)
            
            if data:
                decoded_data = data.decode('utf-8', errors='replace').strip()
                if decoded_data:
                    self.logger.info(f"Received: {decoded_data}")
                    return decoded_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading data: {e}")
            return None
    
    async def listen_continuously(self) -> None:
        """Continuously listen for incoming data."""
        self.logger.info("Starting continuous listening mode...")
        self.running = True
        
        try:
            while self.running:
                data = await self.read_data()
                if data:
                    # Process received data here
                    await self.process_received_data(data)
                else:
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.1)
                    
        except asyncio.CancelledError:
            self.logger.info("Listening cancelled")
        except Exception as e:
            self.logger.error(f"Error in continuous listening: {e}")
    
    async def process_received_data(self, data: str) -> None:
        """Process received data. Override this method for custom processing."""
        # Default implementation just logs the data
        print(f"📥 Received: {data}")
        
        # Example: Echo the data back
        # await self.send_data(f"Echo: {data}")
    
    async def interactive_mode(self) -> None:
        """Interactive mode for sending commands."""
        self.logger.info("Entering interactive mode. Type 'quit' to exit.")
        
        try:
            while True:
                try:
                    # Note: In a real application, you might want to use aioconsole
                    # for proper async input handling
                    command = input("Enter command: ")
                    
                    if command.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if command.strip():
                        await self.send_data(command)
                        
                        # Give some time for response
                        await asyncio.sleep(0.5)
                        
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                    
        except Exception as e:
            self.logger.error(f"Error in interactive mode: {e}")
    
    def stop(self) -> None:
        """Stop the continuous listening."""
        self.running = False
        self.logger.info("Stopping serial client...")


async def main():
    """Main function."""
    # Setup signal handlers for graceful shutdown
    client = None
    
    def signal_handler(signum, frame):
        if client:
            client.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration
        config = SerialConfig()
        
        # Create serial client
        client = AsyncSerialClient(config)
        
        # Connect to device
        if not await client.connect():
            return 1
        
        # Choose mode based on command line arguments
        if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
            # Interactive mode
            await client.interactive_mode()
        else:
            # Continuous listening mode
            listen_task = asyncio.create_task(client.listen_continuously())
            
            # Example: Send a test command after connection
            await asyncio.sleep(1)
            await client.send_data("Hello from Python!")
            
            # Wait for the listening task
            await listen_task
        
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    except Exception as e:
        logging.error(f"Application error: {e}")
        return 1
    finally:
        if client:
            await client.disconnect()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)