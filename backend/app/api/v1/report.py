import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.models.report import Report
from app.services.report_service import generate_report

router = APIRouter()


@router.post("/{company_id}")
def create_report(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> dict:
    try:
        report = generate_report(db, company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"report_id": str(report.id), "download_url": f"/api/report/{company.id}/{report.id}/download"}


@router.get("/{company_id}/{report_id}/download")
def download_report(report_id: uuid.UUID, company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> FileResponse:
    report = db.get(Report, report_id)
    if not report or str(report.company_id) != str(company.id):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report.file_path, media_type="application/pdf", filename=f"{company.name}_health_report.pdf")


@router.get("/{company_id}")
def list_reports(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> list[dict]:
    reports = db.query(Report).filter(Report.company_id == company.id).order_by(Report.created_at.desc()).all()
    return [{"id": str(r.id), "report_type": r.report_type, "created_at": r.created_at.isoformat()} for r in reports]
