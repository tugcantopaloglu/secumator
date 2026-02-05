from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from secumator.core import get_logger, settings
from secumator.core.database import get_db
from secumator.models.scan import Scan, ScanStatus
from secumator.models.schemas import ReportRequest, ReportResponse
from secumator.reports import ReportGenerator
from secumator.reports.sarif import export_sarif

router = APIRouter()
logger = get_logger("api.reports")

_generator: ReportGenerator | None = None

def get_report_generator() -> ReportGenerator:
    global _generator
    if _generator is None:
        _generator = ReportGenerator()
    return _generator


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
        report_path = await get_report_generator().generate(
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
    elif filename.endswith(".sarif"):
        media_type = "application/sarif+json"

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type=media_type,
    )


@router.get("/reports/{scan_id}/sarif")
async def export_sarif_report(
    scan_id: int,
    download: bool = Query(False, description="Download as file instead of JSON response"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Scan must be completed to export SARIF")

    logger.info("exporting_sarif", scan_id=scan.id)

    if download:
        output_dir = Path(settings.report_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"secumator_report_{scan.id}_{timestamp}.sarif"
        sarif_data = export_sarif(scan, scan.findings, output_path)
        return FileResponse(
            path=output_path,
            filename=output_path.name,
            media_type="application/sarif+json",
        )
    else:
        sarif_data = export_sarif(scan, scan.findings)
        return JSONResponse(content=sarif_data)
