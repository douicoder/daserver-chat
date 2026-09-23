from typing import Optional

from pydantic import BaseModel, field_validator


class CreateDirectConversationRequest(BaseModel):
    user_id: str

    @field_validator("user_id")
    @classmethod
    def non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("user_id is required")
        return v.strip()


class CreateGroupConversationRequest(BaseModel):
    name: str
    member_ids: Optional[list[str]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Group name is required")
        if len(v.strip()) > 255:
            raise ValueError("Group name must be at most 255 characters")
        return v.strip()


class AddConversationMemberRequest(BaseModel):
    user_id: str

    @field_validator("user_id")
    @classmethod
    def non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("user_id is required")
        return v.strip()


class UpdateGroupRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Group name is required")
        if len(v.strip()) > 255:
            raise ValueError("Group name must be at most 255 characters")
        return v.strip()
