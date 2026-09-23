import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    encrypted_content = Column(Text, nullable=False)
    nonce = Column(String(32), nullable=False)
    attachment_id = Column(String(36), ForeignKey("attachments.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    sender = relationship("User", back_populates="messages")
    attachment = relationship("Attachment", back_populates="message", uselist=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
