import asyncio
import asyncio.events
import undetected_chromedriver as uc
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime
from faker import Faker
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every

from models.models import JoinMeetingRequest, ChangeLayoutRequest, SendChatMessageRequest
from services.launch_svc import launch_webdriver
from services.meet_svc import join_google_meet, toggle_mute_state, change_meeting_layout, send_chat_message, \
    exit_meeting, toggle_video_state

# TODO: - Join meeting given a meeting url
# - Mute or Unmute itself
# - Change Layouts of the meeting
# - Send chat messages to participants
# - Bonus- Change to a custom background using either image or video
# - Server to Client
# - Start Meeting
# - Stop Meeting
# - Send Chat Message to participants
# - Client to Server
# - Meeting has Started
# - Meeting has ended
# - Participant has joined- Host has joined

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
            "data": "Connected to MeetBot events stream"
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
    await check_participants()
    yield
    driver.quit()


app = FastAPI(title="Meetbot API", version="0.0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def ws_broadcast(event: str, message: dict):
    try:
        await manager.broadcast({
            "type": event,
            "timestamp": datetime.now().isoformat(),
            "data": message
        })
    except Exception as e:
        print(f"Error broadcasting event: {e}")


@app.post("/join_meeting")
async def join_meeting(request: JoinMeetingRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(join_meeting_background, request)
    return {"message": "Meet join operation started"}


async def join_meeting_background(request: JoinMeetingRequest):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, join_google_meet, driver, request.bot_name, request.meeting_url)
    await ws_broadcast("meeting_joined", {
        "meeting_url": request.meeting_url,
        "bot_name": request.bot_name
    })


@app.post("/leave_meeting")
async def leave_meeting(background_tasks: BackgroundTasks):
    background_tasks.add_task(leave_meeting_background)
    return {"message": "Leave meeting operation started"}


async def leave_meeting_background():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, exit_meeting, driver)
    await ws_broadcast("meeting_left", {
        "message": "Bot left meeting"
    })


@app.post("/toggle_mute")
async def toggle_mute(background_tasks: BackgroundTasks):
    background_tasks.add_task(toggle_mute_background)
    return {"message": "Mute toggle operation started"}


async def toggle_mute_background():
    loop = asyncio.get_event_loop()
    mute_status = await loop.run_in_executor(None, toggle_mute_state, driver)
    await ws_broadcast("mute_toggled", {
        "mute_status": mute_status
    })

@app.post("/toggle_video")
async def toggle_video(background_tasks: BackgroundTasks):
    background_tasks.add_task(toggle_video_background)
    return {"message": "Video toggle operation started"}


async def toggle_video_background():
    loop = asyncio.get_event_loop()
    video_status = await loop.run_in_executor(None, toggle_video_state, driver)
    await ws_broadcast("video_toggled", {
        "video_status": video_status
    })

@app.post("/change_layout")
async def change_layout(request: ChangeLayoutRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(change_layout_background, request)
    return {"message": "Layout change operation started"}


async def change_layout_background(request: ChangeLayoutRequest):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, change_meeting_layout, driver, request.layout)
    await ws_broadcast("layout_changed", {
        "layout": request.layout.value
    })


@app.post("/create_screenshot")
async def create_screenshot():
    screenshot = driver.save_screenshot("screenshots/screenshot.png")
    return {"message": "Screenshot created", "screenshot": screenshot}


@app.post("/send_chat_message")
async def send_message(request: SendChatMessageRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_message_background, request)
    return {"message": "Chat message operation started"}


async def send_message_background(request: SendChatMessageRequest):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_chat_message, driver, request.message)
    await ws_broadcast("chat_message_sent", {
        "message": request.message
    })


@repeat_every(seconds=5, raise_exceptions=True)
async def check_participants():
    join_message = driver.execute_script("return window._join_message")
    left_message = driver.execute_script("return window._left_message")
    join_accepted = driver.execute_script("return window._join_accepted")
    if join_accepted:
        await manager.broadcast({
            "type": "bot_accepted",
            "timestamp": datetime.now().isoformat(),
            "data": {"message": "Bot accepted by host"}
        })
        driver.execute_script("window._join_accepted = null")
    if join_message:
        await manager.broadcast({
            "type": "participant_joined",
            "timestamp": datetime.now().isoformat(),
            "data": {"message": join_message}
        })
        driver.execute_script("window._join_message = null")
    if left_message:
        await manager.broadcast({
            "type": "participant_left",
            "timestamp": datetime.now().isoformat(),
            "data": {"message": left_message}
        })
        driver.execute_script("window._left_message = null")


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
        if driver:
            driver.quit()
