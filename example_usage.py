#!/usr/bin/env python3
"""
Example usage of the AsyncSerialClient

This demonstrates how to extend the serial client for custom applications.
"""

import asyncio
import logging
from serial_client import AsyncSerialClient, SerialConfig


class CustomSerialClient(AsyncSerialClient):
    """Custom serial client with application-specific processing."""
    
    async def process_received_data(self, data: str) -> None:
        """Custom data processing - override the base method."""
        print(f"🔄 Processing: {data}")
        
        # Example: Parse specific commands or responses
        if data.startswith("TEMP:"):
            temperature = data.split(":")[1].strip()
            print(f"🌡️  Temperature reading: {temperature}°C")
        elif data.startswith("STATUS:"):
            status = data.split(":")[1].strip()
            print(f"📊 Device status: {status}")
        elif data.startswith("ERROR:"):
            error = data.split(":")[1].strip()
            print(f"⚠️  Error reported: {error}")
        else:
            print(f"📨 General message: {data}")
    
    async def send_command_with_response(self, command: str, timeout: float = 5.0) -> str:
        """Send a command and wait for response."""
        await self.send_data(command)
        
        # Wait for response with timeout
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            response = await self.read_data()
            if response:
                return response
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"No response received within {timeout} seconds")


async def example_automated_commands():
    """Example of automated command sequence."""
    config = SerialConfig("serial_config.json")
    client = CustomSerialClient(config)
    
    try:
        if await client.connect():
            print("Connected! Running automated command sequence...")
            
            # Send a series of commands
            commands = [
                "GET_TEMP",
                "GET_STATUS", 
                "SET_LED ON",
                "GET_VERSION"
            ]
            
            for cmd in commands:
                print(f"Sending: {cmd}")
                try:
                    response = await client.send_command_with_response(cmd)
                    print(f"Response: {response}")
                except TimeoutError:
                    print(f"Timeout waiting for response to: {cmd}")
                
                await asyncio.sleep(1)  # Wait between commands
        
    finally:
        await client.disconnect()


async def example_monitoring_mode():
    """Example of continuous monitoring with periodic commands."""
    config = SerialConfig("serial_config.json")
    client = CustomSerialClient(config)
    
    try:
        if await client.connect():
            print("Starting monitoring mode...")
            
            # Start continuous listening
            listen_task = asyncio.create_task(client.listen_continuously())
            
            # Periodically send status requests
            async def periodic_status():
                while client.running:
                    await asyncio.sleep(10)  # Every 10 seconds
                    await client.send_data("GET_STATUS")
            
            status_task = asyncio.create_task(periodic_status())
            
            # Run both tasks concurrently
            await asyncio.gather(listen_task, status_task)
        
    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    finally:
        client.stop()
        await client.disconnect()


if __name__ == "__main__":
    print("Serial Client Examples")
    print("1. Automated commands")
    print("2. Monitoring mode")
    
    choice = input("Choose example (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(example_automated_commands())
    elif choice == "2":
        asyncio.run(example_monitoring_mode())
    else:
        print("Invalid choice")