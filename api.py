from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import undetected_chromedriver as uc
from services.launch_svc import launch_webdriver
from services.meet_svc import join_google_meet, toggle_mute_state, change_meeting_layout, send_chat_message, exit_meeting, list_participants
from contextlib import asynccontextmanager
from faker import Faker
import json
import asyncio
from datetime import datetime

from models.models import JoinMeetingRequest, ChangeLayoutRequest, SendChatMessageRequest

# TODO: - Join meeting given a meeting url
# - Mute or Unmute itself
# - Change Layouts of the meeting
# - Send chat messages to participants
# - Bonus- Change to a custom background using either image or video

driver = None
fake = Faker()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to MeetBot events stream"
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be closed or broken
                pass

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver
    driver = launch_webdriver()
    yield
    driver.quit()

app = FastAPI(title="Selenium Single-Instance API", version="0.1.0", lifespan=lifespan)

# CORS (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/join_meeting")
async def join_meeting(request: JoinMeetingRequest):
    # Create background task
    asyncio.create_task(join_meeting_background(request))
    return {"message": "Meet join operation started"}

async def join_meeting_background(request: JoinMeetingRequest):
    join_google_meet(driver, request.bot_name, request.meeting_url)
    # Broadcast event when complete
    await manager.broadcast({
        "type": "meeting_joined",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "meeting_url": request.meeting_url,
            "bot_name": request.bot_name
        }
    })

@app.post("/leave_meeting")
async def leave_meeting():
    asyncio.create_task(leave_meeting_background())
    return {"message": "Leave meeting operation started"}

async def leave_meeting_background():
    exit_meeting(driver)
    await manager.broadcast({
        "type": "meeting_left",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/run_script")
async def run_script():
    list_participants(driver)
    return {"message": "Script run operation started"}



@app.post("/toggle_mute")
async def toggle_mute():
    # Create background task
    asyncio.create_task(toggle_mute_background())
    return {"message": "Mute toggle operation started"}

async def toggle_mute_background():
    mute_status = toggle_mute_state(driver)
    # Broadcast event when complete
    await manager.broadcast({
        "type": "mute_toggled",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "mute_status": mute_status
        }
    })

@app.post("/change_layout")
async def change_layout(request: ChangeLayoutRequest):
    # Create background task
    asyncio.create_task(change_layout_background(request))
    return {"message": "Layout change operation started"}

async def change_layout_background(request: ChangeLayoutRequest):
    change_meeting_layout(driver, request.layout)
    # Broadcast event when complete
    await manager.broadcast({
        "type": "layout_changed",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "layout": request.layout
        }
    })

@app.get("/create_screenshot")
async def create_screenshot():
    screenshot = driver.save_screenshot("screenshots/screenshot.png")
    # Broadcast event
    await manager.broadcast({
        "type": "screenshot_created",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "path": "screenshots/screenshot.png"
        }
    })
    return {"message": "Screenshot created", "screenshot": screenshot}

@app.post("/send_chat_message")
async def send_message(request: SendChatMessageRequest):
    # Create background task
    asyncio.create_task(send_message_background(request))
    return {"message": "Chat message operation started"}

async def send_message_background(request: SendChatMessageRequest):
    send_chat_message(driver, request.message)
    # Broadcast event when complete
    await manager.broadcast({
        "type": "chat_message_sent",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "message": request.message
        }
    })


@app.websocket("/events")
async def events_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for streaming events from the MeetBot server.
    Clients can connect to this endpoint to receive real-time updates.
    """
    await manager.connect(websocket)
    try:
        # Send a heartbeat every 30 seconds to keep the connection alive
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )
    finally:
        # Ensure driver is closed even if uvicorn has an error
        if driver:
            driver.quit()
