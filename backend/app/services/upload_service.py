import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.company import Company
from app.models.upload import Upload
from app.utils.file_parser import validate_extension


def save_upload_file(db: Session, company: Company, file: UploadFile, data_category: str) -> Upload:
    ext = validate_extension(file.filename)

    company_dir = Path(settings.UPLOAD_DIR) / str(company.id)
    company_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = company_dir / stored_name

    size = 0
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    with open(dest_path, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                out.close()
                dest_path.unlink(missing_ok=True)
                raise ValueError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit")
            out.write(chunk)

    upload = Upload(
        company_id=company.id,
        filename=file.filename,
        file_path=str(dest_path),
        file_type=ext.lstrip("."),
        data_category=data_category,
        status="uploaded",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def list_uploads(db: Session, company: Company) -> list[Upload]:
    return db.query(Upload).filter(Upload.company_id == company.id).order_by(Upload.created_at.desc()).all()
