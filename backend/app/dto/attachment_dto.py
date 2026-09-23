from typing import Optional

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: str
    original_filename: str
    mime_type: str
    size: int
    created_at: str
    download_url: str
