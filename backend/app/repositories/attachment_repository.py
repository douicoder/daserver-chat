from sqlalchemy.orm import Session

from app.models.attachment import Attachment


class AttachmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, original_filename: str, stored_filename: str, mime_type: str, size: int, storage_path: str, uploader_id: str) -> Attachment:
        attachment = Attachment(
            original_filename=original_filename,
            stored_filename=stored_filename,
            mime_type=mime_type,
            size=size,
            storage_path=storage_path,
            uploader_id=uploader_id,
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def find_by_id(self, attachment_id: str) -> Attachment | None:
        return self.db.query(Attachment).filter(Attachment.id == attachment_id).first()
