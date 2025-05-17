#!/usr/bin/env python3
import asyncio
import json
import sys
import threading
import requests
import websockets
from enum import Enum
from colorama import init, Fore, Style
import time
import shlex

# Initialize colorama for cross-platform colored terminal text
init()

# API connection settings
API_BASE_URL = "http://localhost:8000"
EVENTS_WS_URL = "ws://localhost:8000/events"

class Layout(str, Enum):
    AUTO = "auto"
    TILED = "tiled"
    SPOTLIGHT = "spotlight"
    SIDEBAR = "sidebar"

class MeetBotCLI:
    def __init__(self):
        self.running = True
        self.websocket = None
        self.ws_thread = None
        self.commands = {
            "join": self.join_meeting,
            "leave": self.leave_meeting,
            "mute": self.toggle_mute,
            "layout": self.change_layout,
            "screenshot": self.create_screenshot,
            "chat": self.send_chat_message,
            "help": self.show_help,
            "exit": self.exit,
            "quit": self.exit
        }
        
    async def connect_websocket(self):
        """Connect to the WebSocket server and listen for events"""
        try:
            self.websocket = await websockets.connect(EVENTS_WS_URL)
            print(f"{Fore.GREEN}Connected to MeetBot events stream{Style.RESET_ALL}")
            
            while self.running:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    event = json.loads(message)
                    self._process_event(event)
                except asyncio.TimeoutError:
                    # This is expected, it allows checking self.running
                    continue
                except Exception as e:
                    if self.running:  # Only show error if we're still supposed to be running
                        print(f"{Fore.RED}Error receiving event: {e}{Style.RESET_ALL}")
                        # Try to reconnect
                        await asyncio.sleep(5)
                        try:
                            self.websocket = await websockets.connect(EVENTS_WS_URL)
                            print(f"{Fore.GREEN}Reconnected to MeetBot events stream{Style.RESET_ALL}")
                        except Exception as e:
                            print(f"{Fore.RED}Failed to reconnect: {e}{Style.RESET_ALL}")
                    else:
                        break
        except Exception as e:
            if self.running:  # Only show error if we're still supposed to be running
                print(f"{Fore.RED}WebSocket connection error: {e}{Style.RESET_ALL}")
        finally:
            if self.websocket:
                await self.websocket.close()
                print(f"{Fore.YELLOW}Disconnected from events stream{Style.RESET_ALL}")

    def _process_event(self, event):
        event_type = event.get("type", "unknown")
        timestamp = event.get("timestamp", "")
        data = event.get("data", {})
        
        # Skip heartbeat events - they're just to keep the connection alive
        if event_type == "heartbeat":
            return
            
        # Format timestamp for display if present
        time_str = ""
        if timestamp:
            try:
                # Just extract the time portion and truncate milliseconds for cleaner display
                time_str = timestamp.split("T")[1].split(".")[0]
                time_str = f"[{time_str}] "
            except (IndexError, AttributeError):
                time_str = ""
        
        # Process different event types
        if event_type == "connection_established":
            message = event.get("message", "Connected to event stream")
            print(f"{Fore.CYAN}{time_str}{message}{Style.RESET_ALL}")
            
        elif event_type == "meeting_joined":
            url = data.get("meeting_url", "unknown")
            name = data.get("bot_name", "unknown")
            print(f"{Fore.CYAN}{time_str}Event: Bot '{name}' joined meeting at {url}{Style.RESET_ALL}")
            
        elif event_type == "mute_toggled":
            status = data.get("mute_status", None)
            state = "muted" if status else "unmuted"
            print(f"{Fore.CYAN}{time_str}Event: Microphone {state}{Style.RESET_ALL}")
            
        elif event_type == "layout_changed":
            layout = data.get("layout", "unknown")
            print(f"{Fore.CYAN}{time_str}Event: Layout changed to {layout}{Style.RESET_ALL}")
            
        elif event_type == "screenshot_created":
            path = data.get("path", "unknown")
            print(f"{Fore.CYAN}{time_str}Event: Screenshot saved to {path}{Style.RESET_ALL}")
            
        elif event_type == "chat_message_sent":
            message = data.get("message", "")
            print(f"{Fore.CYAN}{time_str}Event: Chat message sent: \"{message}\"{Style.RESET_ALL}")
            
        else:
            print(f"{Fore.CYAN}{time_str}Event: {event_type} - {json.dumps(data)}{Style.RESET_ALL}")
    
    def start_websocket(self):
        """Start the WebSocket connection in a background thread"""
        # Define the async event loop function
        def run_event_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect_websocket())
            loop.close()
        
        # Start the event loop in a thread
        self.ws_thread = threading.Thread(target=run_event_loop)
        self.ws_thread.daemon = True  # Thread will exit when main program exits
        self.ws_thread.start()
    
    def stop_websocket(self):
        """Stop the WebSocket connection"""
        self.running = False
        if self.ws_thread:
            self.ws_thread.join(2.0)  # Wait for the thread to end
    
    def join_meeting(self, args):
        """Join a Google Meet meeting"""
        if len(args) < 2 or args[0] == "help":
            print("Usage: join <meeting_url> <bot_name>")
            print("Example: join https://meet.google.com/abc-defg-hij MeetBot")
            return
        
        meeting_url = args[0]
        bot_name = args[1]
        
        response = requests.post(
            f"{API_BASE_URL}/join_meeting",
            json={"meeting_url": meeting_url, "bot_name": bot_name}
        )
        if response.status_code == 200:
            print(f"{Fore.GREEN}Successfully initiated join meeting operation{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error: {response.status_code}{Style.RESET_ALL}")
            print(response.json())

    def leave_meeting(self, args):
        """Leave a Google Meet meeting"""
        if args and args[0] == "help":
            print("Usage: leave")
            print("Leaves the current Google Meet meeting")
            return
        
        response = requests.post(f"{API_BASE_URL}/leave_meeting")
        if response.status_code == 200:
            print(f"{Fore.GREEN}Successfully initiated leave meeting operation{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error: {response.status_code}{Style.RESET_ALL}")
            print(response.json())
            

    def toggle_mute(self, args):
        """Toggle the microphone mute state"""
        if args and args[0] == "help":
            print("Usage: mute")
            print("Toggles the microphone mute state")
            return
            
        response = requests.post(f"{API_BASE_URL}/toggle_mute")
        if response.status_code == 200:
            data = response.json()
            mute_status = data.get("mute_status", "unknown")
            state = "muted" if mute_status else "unmuted"
            print(f"{Fore.GREEN}Microphone toggled: {state}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error: {response.status_code}{Style.RESET_ALL}")
            print(response.json())

    def change_layout(self, args):
        """Change the meeting layout"""
        if not args or args[0] == "help":
            print("Usage: layout <layout_type>")
            print("Available layouts: auto, tiled, spotlight, sidebar")
            print("Example: layout tiled")
            return
            
        layout = args[0].lower()
        if layout not in [l.value for l in Layout]:
            print(f"{Fore.RED}Invalid layout: {layout}{Style.RESET_ALL}")
            print(f"Available layouts: {', '.join([l.value for l in Layout])}")
            return
            
        response = requests.post(
            f"{API_BASE_URL}/change_layout",
            json={"layout": layout}
        )
        if response.status_code == 200:
            print(f"{Fore.GREEN}Successfully changed layout to {layout}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error: {response.status_code}{Style.RESET_ALL}")
            print(response.json())

    def create_screenshot(self, args):
        """Take a screenshot of the current meeting view"""
        if args and args[0] == "help":
            print("Usage: screenshot")
            print("Takes a screenshot of the current meeting view")
            return
            
        response = requests.get(f"{API_BASE_URL}/create_screenshot")
        if response.status_code == 200:
            print(f"{Fore.GREEN}Screenshot created successfully{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error: {response.status_code}{Style.RESET_ALL}")
            print(response.json())

    def send_chat_message(self, args):
        """Send a message in the meeting chat"""
        if not args or args[0] == "help":
            print("Usage: chat <message>")
            print("Example: chat Hello everyone!")
            return
            
        # Join all args as the message
        message = " ".join(args)
            
        response = requests.post(
            f"{API_BASE_URL}/send_chat_message",
            json={"message": message}
        )
        if response.status_code == 200:
            print(f"{Fore.GREEN}Chat message sent successfully{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error: {response.status_code}{Style.RESET_ALL}")
            print(response.json())
    
    def show_help(self, args=None):
        """Show help information"""
        print(f"{Fore.GREEN}MeetBot CLI - Control Google Meet meetings{Style.RESET_ALL}")
        print()
        print("Available commands:")
        print("  join <meeting_url> <bot_name> - Join a Google Meet meeting")
        print("  mute - Toggle the microphone mute state")
        print("  layout <layout_type> - Change the meeting layout (auto, tiled, spotlight, sidebar)")
        print("  screenshot - Take a screenshot of the current meeting view")
        print("  chat <message> - Send a message in the meeting chat")
        print("  help - Show this help information")
        print("  <command> help - Show help for a specific command")
        print("  exit/quit - Exit the program")
        print()
        print(f"Type {Fore.YELLOW}<command> help{Style.RESET_ALL} for more information about a specific command")
    
    def exit(self, args=None):
        """Exit the program"""
        self.running = False
        return True
        
    def parse_and_execute(self, command_line):
        """Parse and execute a command"""
        # Skip empty lines
        if not command_line.strip():
            return False
            
        # Parse command line
        try:
            args = shlex.split(command_line)
        except ValueError as e:
            print(f"{Fore.RED}Error parsing command: {e}{Style.RESET_ALL}")
            return False
            
        command = args[0].lower()
        args = args[1:] if len(args) > 1 else []
        
        # Handle special help case
        if command == "help":
            self.show_help()
            return False
            
        # Execute command if it exists
        if command in self.commands:
            return self.commands[command](args)
        else:
            print(f"{Fore.RED}Unknown command: {command}{Style.RESET_ALL}")
            print(f"Type {Fore.YELLOW}help{Style.RESET_ALL} for a list of available commands")
            return False
    
    def run_interactive(self):
        """Run the interactive CLI"""
        # Start WebSocket connection
        self.start_websocket()
        
        try:
            print(f"{Fore.GREEN}MeetBot CLI started. Type 'help' for available commands.{Style.RESET_ALL}")
            print(f"Connected to API at {API_BASE_URL}")
            
            # Main input loop
            while self.running:
                try:
                    command = input(f"{Fore.GREEN}meetbot> {Style.RESET_ALL}")
                    should_exit = self.parse_and_execute(command)
                    if should_exit:
                        break
                except EOFError:
                    # Handle Ctrl+D
                    print("\nExiting...")
                    self.running = False
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    print("\nUse 'exit' or 'quit' to exit the program")
                    continue
        finally:
            # Clean up
            self.stop_websocket()
            print(f"{Fore.YELLOW}MeetBot CLI exited.{Style.RESET_ALL}")

def main():
    # Create and run the CLI
    cli = MeetBotCLI()
    cli.run_interactive()

if __name__ == "__main__":
    main() 