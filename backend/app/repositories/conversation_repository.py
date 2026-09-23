from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMember


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, conv_type: str, name=None, owner_id=None) -> Conversation:
        conv = Conversation(type=conv_type, name=name, owner_id=owner_id)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def find_by_id(self, conversation_id: str) -> Conversation | None:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def list_for_user(self, user_id: str) -> list[Conversation]:
        return (
            self.db.query(Conversation)
            .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
            .filter(ConversationMember.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def find_direct_between(self, user_a: str, user_b: str) -> Conversation | None:
        """Return an existing DIRECT conversation containing exactly these two users."""
        candidates = (
            self.db.query(Conversation)
            .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
            .filter(Conversation.type == "DIRECT")
            .filter(ConversationMember.user_id.in_([user_a, user_b]))
            .all()
        )
        for conv in candidates:
            member_ids = {m.user_id for m in conv.members}
            if member_ids == {user_a, user_b}:
                return conv
        return None

    def is_member(self, conversation_id: str, user_id: str) -> bool:
        return (
            self.db.query(ConversationMember)
            .filter(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
            .first()
            is not None
        )

    def add_member(self, conversation_id: str, user_id: str) -> ConversationMember:
        member = ConversationMember(conversation_id=conversation_id, user_id=user_id)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, conversation_id: str, user_id: str) -> None:
        self.db.query(ConversationMember).filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id,
        ).delete()
        self.db.commit()

    def touch(self, conversation: Conversation) -> None:
        # Bump updated_at so recent conversations sort first.
        from datetime import datetime, timezone
        conversation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conversation)
