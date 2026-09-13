from datetime import datetime

from pydantic import BaseModel, Field


class ChatUser(BaseModel):
    id: int
    username: str
    role: str
    enabled: bool
    online: bool = False

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    receiver_id: int
    content: str = Field(min_length=1, max_length=1000)


class ChatMessage(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    receiver_id: int
    receiver_name: str
    content: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
