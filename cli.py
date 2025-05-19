import json
import requests
import threading
import typer
import websocket
from enum import Enum
from rich import print
from typing import Optional


class Layout(str, Enum):
    AUTO = "auto"
    TILED = "tiled"
    SPOTLIGHT = "spotlight"
    SIDEBAR = "sidebar"

API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/events"

app = typer.Typer(help="Meetbot CLI with WebSocket support.")

@app.command()
def join_meeting(
    meeting_url: str = typer.Argument(
        None, help="Meeting URL to join."
    ),
    bot_name: str = typer.Argument(
        'Sidekick', help="Name of the bot to join the meeting as."
    )
):
    """Join a meeting with meeting_url and bot_name"""
    if not meeting_url:
        app(["join-meeting", "--help"], standalone_mode=False)
        return
    response = requests.post(
        f"{API_BASE_URL}/join_meeting",
        json={"meeting_url": meeting_url, "bot_name": bot_name}
    )
    if response.status_code == 200:
        print(f"[green]Meeting join operation initiated with bot {bot_name} at[/green] [blue]{meeting_url}[/blue]")
    else:
        print(f"[bold red]Meeting join operation failed: {response.status_code}[/bold red]")
    
@app.command()
def leave_meeting():
    """Leave the current meeting."""
    response = requests.post(f"{API_BASE_URL}/leave_meeting")
    if response.status_code == 200:
        print("[green]Meeting leave operation initiated[/green]")
    else:
        print(f"[bold red]Meeting leave operation failed: {response.status_code}[/bold red]")

@app.command()
def toggle_mute():
    """Toggle the mute state of the current meeting."""
    response = requests.post(f"{API_BASE_URL}/toggle_mute")
    if response.status_code == 200:
        print("[green]Mute toggle operation initiated[/green]")
    else:
        print(f"[bold red]Mute toggle operation failed: {response.status_code}[/bold red]")

@app.command()
def toggle_video():
    """Toggle the video state of the current meeting."""
    response = requests.post(f"{API_BASE_URL}/toggle_video")
    if response.status_code == 200:
        print("[green]Video toggle operation initiated[/green]")
    else:
        print(f"[bold red]Video toggle operation failed: {response.status_code}[/bold red]")

@app.command()
def send_message(
    message: list[str] = typer.Argument(
        None, help="Chat message to send. Can include spaces."
    )
):
    """Send a message to the current meeting."""
    if not message:
        app(["send-message", "--help"], standalone_mode=False)
        return
    full_message = " ".join(message)
    response = requests.post(f"{API_BASE_URL}/send_chat_message", json={"message": full_message})
    if response.status_code == 200:
        print("[green]Message sent successfully[/green]")
    else:
        print(f"[bold red]Message sending failed: {response.status_code}[/bold red]")

@app.command()
def change_layout(layout: Layout = typer.Argument(
        Layout.AUTO, help="Layout to change to."
    )
):
    """Change the layout of the current meeting."""
    response = requests.post(f"{API_BASE_URL}/change_layout", json={"layout": layout})
    if response.status_code == 200:
        print("[green]Layout changed successfully[/green]")
    else:
        print(f"[bold red]Layout change failed: {response.status_code}[/bold red]")


@app.command()
def create_screenshot():
    """Create a screenshot of the current window."""
    response = requests.post(f"{API_BASE_URL}/create_screenshot")
    if response.status_code == 200:
        print("[green]Screenshot created successfully[/green]")
    else:
        print(response.json())
        print(f"[bold red]Screenshot creation failed: {response.status_code}[/bold red]")


@app.command()
def console(
    api_url: str = typer.Option(
        API_BASE_URL, "--api-url", help="API server URL to connect to."
    ),
    ws_url: str = typer.Option(
        WS_URL, "--ws-url", help="WebSocket server URL to connect to."
    )
):
    """Launch Meetbot CLI session with WebSocket logging."""
    # WebSocket event handlers
    def on_message(ws, message):
        parsed_message = json.loads(message)
        if parsed_message.get("type") == "heartbeat":
            return
        print(f'[WS] [{parsed_message.get("timestamp")}] event={parsed_message.get("type")} data={parsed_message.get("data")}')

    def on_error(ws, error):
        print(f"[red]WS error: {error}[/red]")

    def on_close(ws, close_status_code, close_msg):
        print(f"[yellow]WS connection closed: code={close_status_code}, message={close_msg}[/yellow]")

    def on_open(ws):
        print(f"[blue]Connected to WS server: {ws_url}[/blue]")

    # Set the API base URL to global variable
    global API_BASE_URL
    API_BASE_URL = api_url

    # Start WebSocket in background thread
    ws_app = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws_thread = threading.Thread(target=ws_app.run_forever, kwargs={"reconnect": 5}, daemon=True)
    ws_thread.start()

    typer.echo("\nMeetbot CLI. Type 'help' to see available commands, or 'exit' to quit.\n")
    
    while True:
        try:
            cmd = typer.prompt("cli> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!\n")
            break

        cmd = cmd.strip()
        if cmd.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        elif cmd.lower() in ("help", "?"):
            app(["--help"], standalone_mode=False)
        elif cmd.lower() in "console":
            print("You are already in the console!")
        else:
            args = cmd.split()
            try:
                app(args, standalone_mode=False)
            except Exception as e:
                print(f"[red]Error: {e}[/red]")

    # Clean up WebSocket
    ws_app.close()
    ws_thread.join(timeout=1)

if __name__ == "__main__":
    app()
