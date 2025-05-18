from enum import Enum
from pydantic import BaseModel

class JoinMeetingRequest(BaseModel):
    meeting_url: str
    bot_name: str

class Layout(Enum):
    AUTO = "auto"
    TILED = "tiled"
    SPOTLIGHT = "spotlight"
    SIDEBAR = "sidebar"

class ChangeLayoutRequest(BaseModel):
    layout: Layout

class SendChatMessageRequest(BaseModel):
    message: str
