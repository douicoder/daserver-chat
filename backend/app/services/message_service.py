import logging

from app.database.database import SessionLocal
from app.repositories.message_repository import MessageRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.security.encryption import encrypt, decrypt
from app.exceptions.exceptions import ValidationError, AttachmentError

logger = logging.getLogger(__name__)


class MessageService:
    def send_message(
        self,
        sender_id: str,
        content: str | None,
        attachment_id: str | None = None,
        conversation_id: str | None = None,
    ) -> dict:
        db = SessionLocal()
        try:
            if not content and not attachment_id:
                raise ValidationError("A message must contain content, an attachment, or both")

            if conversation_id:
                from app.repositories.conversation_repository import ConversationRepository
                from app.exceptions.exceptions import (
                    ConversationNotFoundError,
                    NotConversationMemberError,
                )
                conv_repo = ConversationRepository(db)
                conv = conv_repo.find_by_id(conversation_id)
                if not conv:
                    raise ConversationNotFoundError("Conversation does not exist")
                if not conv_repo.is_member(conversation_id, sender_id):
                    raise NotConversationMemberError("You are not a member of this conversation")

            verified_attachment = None
            if attachment_id:
                attach_repo = AttachmentRepository(db)
                attachment = attach_repo.find_by_id(attachment_id)

                if not attachment:
                    raise AttachmentError("Attachment not found")
                if attachment.uploader_id != sender_id:
                    raise AttachmentError("You can only attach your own files")
                if attachment.message:
                    raise AttachmentError("Attachment already used in another message")
                verified_attachment = attachment

            text_to_encrypt = content if content else ""
            encrypted_content, nonce = encrypt(text_to_encrypt)

            msg_repo = MessageRepository(db)
            message = msg_repo.create(
                sender_id=sender_id,
                encrypted_content=encrypted_content,
                nonce=nonce,
                attachment_id=attachment_id,
                conversation_id=conversation_id,
            )

            if conversation_id:
                from app.repositories.conversation_repository import ConversationRepository
                conv_repo = ConversationRepository(db)
                conv = conv_repo.find_by_id(conversation_id)
                if conv:
                    conv_repo.touch(conv)

            logger.info("Message sent by user %s", sender_id)
            return self._format_message(message, decrypt_text=True)
        finally:
            db.close()

    def get_messages(self, page: int, limit: int) -> dict:
        db = SessionLocal()
        try:
            msg_repo = MessageRepository(db)
            total = msg_repo.count_all()
            messages = msg_repo.list_paginated(page, limit)

            formatted = []
            for msg in messages:
                formatted.append(self._format_message(msg, decrypt_text=True))

            return {
                "messages": formatted,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
                },
            }
        finally:
            db.close()

    def get_conversation_messages(
        self, user_id: str, conversation_id: str, page: int, limit: int
    ) -> dict:
        from app.repositories.conversation_repository import ConversationRepository
        from app.exceptions.exceptions import (
            ConversationNotFoundError,
            NotConversationMemberError,
        )
        db = SessionLocal()
        try:
            conv_repo = ConversationRepository(db)
            conv = conv_repo.find_by_id(conversation_id)
            if not conv:
                raise ConversationNotFoundError("Conversation does not exist")
            if not conv_repo.is_member(conversation_id, user_id):
                raise NotConversationMemberError("You are not a member of this conversation")

            msg_repo = MessageRepository(db)
            total = msg_repo.count_for_conversation(conversation_id)
            messages = msg_repo.list_for_conversation(conversation_id, page, limit)

            formatted = [self._format_message(m, decrypt_text=True) for m in messages]
            return {
                "messages": formatted,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
                },
            }
        finally:
            db.close()

    def _format_message(self, message, decrypt_text: bool = False) -> dict:
        content = None
        if message.encrypted_content:
            if decrypt_text:
                try:
                    content = decrypt(message.encrypted_content, message.nonce)
                except Exception:
                    content = None
            else:
                content = message.encrypted_content

        attachment_data = None
        if message.attachment:
            attachment_data = {
                "id": message.attachment.id,
                "original_filename": message.attachment.original_filename,
                "mime_type": message.attachment.mime_type,
                "size": message.attachment.size,
            }

        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "sender_username": message.sender.username if message.sender else "unknown",
            "content": content,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "attachment": attachment_data,
        }
