from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from secumator.core import get_logger, settings
from secumator.core.database import get_db
from secumator.models.scan import Scan, ScanStatus
from secumator.models.schemas import ReportRequest, ReportResponse
from secumator.reports import ReportGenerator

router = APIRouter()
logger = get_logger("api.reports")
generator = ReportGenerator()


@router.post("/reports", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    result = await db.execute(
        select(Scan).options(selectinload(Scan.findings)).where(Scan.id == request.scan_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Scan must be completed to generate report")

    logger.info("generating_report", scan_id=scan.id, format=request.format)

    try:
        report_path = await generator.generate(
            scan=scan,
            findings=scan.findings,
            format=request.format,
            template=request.template,
            include_executive_summary=request.include_executive_summary,
            include_ai_analysis=request.include_ai_analysis,
        )

        return ReportResponse(
            scan_id=scan.id,
            format=request.format,
            filename=report_path.name,
            download_url=f"{settings.api_prefix}/reports/download/{report_path.name}",
            generated_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error("report_generation_failed", scan_id=scan.id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/reports/download/{filename}")
async def download_report(filename: str):
    report_path = Path(settings.report_output_dir) / filename

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    if not report_path.is_relative_to(settings.report_output_dir):
        raise HTTPException(status_code=403, detail="Access denied")

    media_type = "application/pdf"
    if filename.endswith(".html"):
        media_type = "text/html"
    elif filename.endswith(".json"):
        media_type = "application/json"

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type=media_type,
    )
