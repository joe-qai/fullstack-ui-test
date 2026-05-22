from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from db.database import get_db
from models.report import Report
from models.test_task import TestTask
from schemas.report import ReportMetadata, ReportListResponse

from sqlalchemy import desc

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports", response_model=list[ReportListResponse])
def list_reports(db: Session = Depends(get_db)):
    rows = db.query(
        Report.id,
        Report.task_id,
        Report.name,
        Report.created_at,
        TestTask.status.label("task_status"),
    ).outerjoin(TestTask, Report.task_id == TestTask.id).order_by(desc(Report.created_at)).all()
    return [
        ReportListResponse(
            id=row.id,
            task_id=row.task_id,
            name=row.name,
            created_at=row.created_at,
            task_status=row.task_status,
        )
        for row in rows
    ]


@router.get("/tasks/{task_id}/report")
def get_task_report(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    report = db.query(Report).filter(Report.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return Response(content=report.content, media_type="text/html")


@router.get("/tasks/{task_id}/report/download")
def download_report(task_id: str, format: str = "html", db: Session = Depends(get_db)):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    report = db.query(Report).filter(Report.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "pdf":
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=report.content).write_pdf()
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=report_{task_id}.pdf"},
            )
        except ImportError:
            raise HTTPException(status_code=500, detail="weasyprint not installed")

    return Response(
        content=report.content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=report_{task_id}.html"},
    )


class BatchDeleteReportsRequest(BaseModel):
    ids: List[str]


@router.delete("/reports/{report_id}")
def delete_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"message": "Report deleted"}


@router.post("/reports/batch-delete")
def batch_delete_reports(req: BatchDeleteReportsRequest, db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.id.in_(req.ids)).all()
    for r in reports:
        db.delete(r)
    db.commit()
    return {"message": f"Deleted {len(reports)} reports", "count": len(reports)}


@router.get("/reports/{report_id}/download")
def download_report_by_id(report_id: str, format: str = "html", db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "pdf":
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=report.content).write_pdf()
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={report.name or report_id}.pdf"},
            )
        except ImportError:
            raise HTTPException(status_code=500, detail="weasyprint not installed")

    return Response(
        content=report.content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={report.name or report_id}.html"},
    )


@router.get("/reports/{report_id}/view")
def view_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(content=report.content, media_type="text/html")
