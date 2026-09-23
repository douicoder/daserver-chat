import logging

from app.database.database import SessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.exceptions.exceptions import (
    ConversationError,
    ConversationNotFoundError,
    NotConversationMemberError,
    NotGroupOwnerError,
    UserNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class ConversationService:
    def _format(self, conv) -> dict:
        members = [
            {"id": m.user_id, "username": m.user.username if m.user else "unknown"}
            for m in (conv.members or [])
        ]
        return {
            "id": conv.id,
            "type": conv.type,
            "name": conv.name,
            "owner_id": conv.owner_id,
            "members": members,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        }

    def _get_or_404(self, repo: ConversationRepository, conversation_id: str):
        conv = repo.find_by_id(conversation_id)
        if not conv:
            raise ConversationNotFoundError("Conversation does not exist")
        return conv

    def _require_member(self, repo: ConversationRepository, conv, user_id: str):
        if not repo.is_member(conv.id, user_id):
            raise NotConversationMemberError("You are not a member of this conversation")

    def list_conversations(self, user_id: str) -> list[dict]:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            return [self._format(c) for c in repo.list_for_user(user_id)]
        finally:
            db.close()

    def get_conversation(self, user_id: str, conversation_id: str) -> dict:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            conv = self._get_or_404(repo, conversation_id)
            self._require_member(repo, conv, user_id)
            return self._format(conv)
        finally:
            db.close()

    def create_direct(self, user_id: str, other_user_id: str) -> tuple[dict, bool]:
        if other_user_id == user_id:
            raise ValidationError(
                "You cannot create a direct conversation with yourself",
                code="DIRECT_CONVERSATION_WITH_SELF",
            )
        db = SessionLocal()
        try:
            users = UserRepository(db)
            if not users.find_by_id(other_user_id):
                raise UserNotFoundError("Target user does not exist")
            repo = ConversationRepository(db)
            existing = repo.find_direct_between(user_id, other_user_id)
            if existing:
                return self._format(existing), False
            conv = repo.create("DIRECT")
            repo.add_member(conv.id, user_id)
            repo.add_member(conv.id, other_user_id)
            db.refresh(conv)
            logger.info("Direct conversation created: %s", conv.id)
            return self._format(conv), True
        finally:
            db.close()

    def create_group(self, user_id: str, name: str, member_ids: list[str] | None) -> dict:
        member_ids = list(dict.fromkeys(member_ids or []))  # dedupe, keep order
        if user_id in member_ids:
            member_ids.remove(user_id)
        member_ids.append(user_id)
        if len(member_ids) < 2:
            raise ValidationError(
                "A group must have at least 2 members",
                code="GROUP_TOO_SMALL",
            )
        db = SessionLocal()
        try:
            users = UserRepository(db)
            for mid in member_ids:
                if not users.find_by_id(mid):
                    raise UserNotFoundError(f"User does not exist: {mid}")
            repo = ConversationRepository(db)
            conv = repo.create("GROUP", name=name, owner_id=user_id)
            for mid in member_ids:
                repo.add_member(conv.id, mid)
            db.refresh(conv)
            logger.info("Group conversation created: %s", conv.id)
            return self._format(conv)
        finally:
            db.close()

    def rename_group(self, user_id: str, conversation_id: str, name: str) -> dict:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            conv = self._get_or_404(repo, conversation_id)
            if conv.type != "GROUP":
                raise ConversationError(
                    "Only group conversations can be renamed",
                    code="INVALID_CONVERSATION_TYPE",
                )
            if conv.owner_id != user_id:
                raise NotGroupOwnerError("Only the group owner can rename the group")
            conv.name = name
            db.commit()
            db.refresh(conv)
            return self._format(conv)
        finally:
            db.close()

    def add_member(self, user_id: str, conversation_id: str, new_user_id: str) -> dict:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            conv = self._get_or_404(repo, conversation_id)
            if conv.type != "GROUP":
                raise ConversationError(
                    "Only group conversations support members",
                    code="INVALID_CONVERSATION_TYPE",
                )
            if conv.owner_id != user_id:
                raise NotGroupOwnerError("Only the group owner can add members")
            users = UserRepository(db)
            if not users.find_by_id(new_user_id):
                raise UserNotFoundError("Target user does not exist")
            if repo.is_member(conv.id, new_user_id):
                raise ConversationError(
                    "User is already a member",
                    code="USER_ALREADY_MEMBER",
                )
            repo.add_member(conv.id, new_user_id)
            db.refresh(conv)
            return self._format(conv)
        finally:
            db.close()

    def remove_member(self, user_id: str, conversation_id: str, target_user_id: str) -> dict:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            conv = self._get_or_404(repo, conversation_id)
            if conv.type != "GROUP":
                raise ConversationError(
                    "Only group conversations support members",
                    code="INVALID_CONVERSATION_TYPE",
                )
            if conv.owner_id != user_id:
                raise NotGroupOwnerError("Only the group owner can remove members")
            if target_user_id == conv.owner_id:
                raise ConversationError(
                    "The group owner cannot be removed",
                    code="CANNOT_REMOVE_OWNER",
                )
            if not repo.is_member(conv.id, target_user_id):
                raise ConversationError(
                    "Target user is not a member",
                    code="USER_NOT_MEMBER",
                )
            repo.remove_member(conv.id, target_user_id)
            db.refresh(conv)
            return self._format(conv)
        finally:
            db.close()

    def leave_group(self, user_id: str, conversation_id: str) -> None:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            conv = self._get_or_404(repo, conversation_id)
            if conv.type != "GROUP":
                raise ConversationError(
                    "Only group conversations can be left",
                    code="INVALID_CONVERSATION_TYPE",
                )
            if not repo.is_member(conv.id, user_id):
                raise NotConversationMemberError("You are not a member of this conversation")
            if conv.owner_id == user_id:
                raise ConversationError(
                    "The group owner cannot leave the group",
                    code="CANNOT_LEAVE_AS_OWNER",
                )
            repo.remove_member(conv.id, user_id)
        finally:
            db.close()
