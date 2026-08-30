import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.upload import UploadOut, DATA_CATEGORIES
from app.services import upload_service
from app.services.data_processing_service import process_upload_by_id

router = APIRouter()


@router.post("", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    background_tasks: BackgroundTasks,
    company_id: uuid.UUID = Form(...),
    data_category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadOut:
    company = db.get(Company, company_id)
    if not company or company.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    if data_category not in DATA_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"data_category must be one of {DATA_CATEGORIES}")

    try:
        upload = upload_service.save_upload_file(db, company, file, data_category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    background_tasks.add_task(process_upload_by_id, upload.id)
    return UploadOut.model_validate(upload)


@router.get("", response_model=list[UploadOut])
def list_uploads(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> list[UploadOut]:
    uploads = upload_service.list_uploads(db, company)
    return [UploadOut.model_validate(u) for u in uploads]
