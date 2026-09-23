from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.config import Config


class SendMessageRequest(BaseModel):
    content: Optional[str] = None
    attachment_id: Optional[str] = None
    # Required for Socket.IO send_message (conversation in URL for REST).
    conversation_id: Optional[str] = None

    @field_validator("content")
    @classmethod
    def strip_content(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > Config.MAX_MESSAGE_LENGTH:
                raise ValueError(f"Message exceeds maximum length of {Config.MAX_MESSAGE_LENGTH} characters")
        return v

    def model_post_init(self, __context):
        if not self.content and not self.attachment_id:
            raise ValueError("A message must contain content, an attachment, or both")


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    sender_username: str
    content: Optional[str] = None
    created_at: str
    attachment: Optional[dict] = None
