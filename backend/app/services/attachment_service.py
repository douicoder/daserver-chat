import logging
import os

from app.database.database import SessionLocal
from app.repositories.attachment_repository import AttachmentRepository
from app.storage import file_storage

logger = logging.getLogger(__name__)


class AttachmentService:
    def upload(self, file_bytes: bytes, original_filename: str, uploader_id: str) -> dict:
        db = SessionLocal()
        try:
            mime_type, size = file_storage.validate_file(file_bytes, original_filename)
            stored_filename = file_storage.generate_stored_filename(original_filename)
            storage_path = file_storage.save_file(file_bytes, stored_filename)

            attach_repo = AttachmentRepository(db)
            attachment = attach_repo.create(
                original_filename=original_filename,
                stored_filename=stored_filename,
                mime_type=mime_type,
                size=size,
                storage_path=storage_path,
                uploader_id=uploader_id,
            )

            logger.info("File uploaded by %s: %s (%d bytes)", uploader_id, original_filename, size)
            return {
                "id": attachment.id,
                "original_filename": attachment.original_filename,
                "mime_type": attachment.mime_type,
                "size": attachment.size,
                "created_at": attachment.created_at.isoformat(),
                "download_url": f"/api/attachments/{attachment.id}",
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_attachment(self, attachment_id: str) -> dict | None:
        db = SessionLocal()
        try:
            attach_repo = AttachmentRepository(db)
            attachment = attach_repo.find_by_id(attachment_id)
            if not attachment:
                return None
            return {
                "id": attachment.id,
                "original_filename": attachment.original_filename,
                "mime_type": attachment.mime_type,
                "size": attachment.size,
                "storage_path": attachment.storage_path,
                "stored_filename": attachment.stored_filename,
            }
        finally:
            db.close()

    def stream_file(self, attachment_id: str) -> tuple:
        """Returns (file_path, original_filename, mime_type) or raises."""
        attachment = self.get_attachment(attachment_id)
        if not attachment:
            return None

        file_path = file_storage.get_file_path(attachment["stored_filename"])
        if not os.path.isfile(file_path):
            return None

        return file_path, attachment["original_filename"], attachment["mime_type"]
