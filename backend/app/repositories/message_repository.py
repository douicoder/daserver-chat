from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, sender_id: str, encrypted_content: bytes, nonce: bytes, attachment_id: str | None = None, conversation_id: str | None = None) -> Message:
        msg = Message(
            sender_id=sender_id,
            encrypted_content=encrypted_content,
            nonce=nonce,
            attachment_id=attachment_id,
            conversation_id=conversation_id,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def find_by_id(self, message_id: str) -> Message | None:
        return self.db.query(Message).filter(Message.id == message_id).first()

    def list_paginated(self, page: int, limit: int) -> list[Message]:
        offset = (page - 1) * limit
        return (
            self.db.query(Message)
            .order_by(Message.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_all(self) -> int:
        return self.db.query(Message).count()

    def count_for_conversation(self, conversation_id: str) -> int:
        return self.db.query(Message).filter(Message.conversation_id == conversation_id).count()

    def list_for_conversation(self, conversation_id: str, page: int, limit: int) -> list[Message]:
        offset = (page - 1) * limit
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
