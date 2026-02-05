from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from secumator.core import get_logger
from secumator.core.database import get_db
from secumator.models.scan import Scan, ScanStatus, ScanType, Finding
from secumator.models.schemas import ScanCreate, ScanResponse, ScanListResponse, FindingResponse
from secumator.scanners import ScanEngine

router = APIRouter()
logger = get_logger("api.scans")
engine = ScanEngine()


async def run_scan_background(scan_id: int):
    from secumator.core.database import async_session_factory
    async with async_session_factory() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan:
            await engine.run_scan(scan, db)


@router.post("/scans", response_model=ScanResponse, status_code=201)
async def create_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ScanResponse:
    logger.info("creating_scan", target=scan_data.target, type=scan_data.scan_type)

    scan = Scan(
        target=scan_data.target,
        scan_type=ScanType(scan_data.scan_type),
        profile=scan_data.profile,
        options=scan_data.options,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    background_tasks.add_task(run_scan_background, scan.id)

    return ScanResponse(
        id=scan.id,
        target=scan.target,
        scan_type=scan.scan_type.value,
        status=scan.status.value,
        profile=scan.profile,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        created_at=scan.created_at,
        findings_count=0,
    )


@router.get("/scans", response_model=ScanListResponse)
async def list_scans(
    status: str | None = Query(None),
    scan_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ScanListResponse:
    query = select(Scan).options(selectinload(Scan.findings))

    if status:
        query = query.where(Scan.status == ScanStatus(status))
    if scan_type:
        query = query.where(Scan.scan_type == ScanType(scan_type))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Scan.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    scans = result.scalars().all()

    items = [
        ScanResponse(
            id=s.id,
            target=s.target,
            scan_type=s.scan_type.value,
            status=s.status.value,
            profile=s.profile,
            started_at=s.started_at,
            completed_at=s.completed_at,
            error_message=s.error_message,
            created_at=s.created_at,
            findings_count=len(s.findings),
        )
        for s in scans
    ]

    return ScanListResponse(total=total, items=items)


@router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int, db: AsyncSession = Depends(get_db)) -> ScanResponse:
    result = await db.execute(
        select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    findings = [
        FindingResponse(
            id=f.id,
            title=f.title,
            severity=f.severity.value,
            description=f.description,
            evidence=f.evidence,
            recommendation=f.recommendation,
            cve_id=f.cve_id,
            cvss_score=f.cvss_score,
            affected_component=f.affected_component,
            source_tool=f.source_tool,
            created_at=f.created_at,
        )
        for f in scan.findings
    ]

    return ScanResponse(
        id=scan.id,
        target=scan.target,
        scan_type=scan.scan_type.value,
        status=scan.status.value,
        profile=scan.profile,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        created_at=scan.created_at,
        findings_count=len(findings),
        findings=findings,
    )


@router.delete("/scans/{scan_id}", status_code=204)
async def delete_scan(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status == ScanStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Cannot delete a running scan")

    await db.delete(scan)
    await db.commit()


@router.post("/scans/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(scan_id: int, db: AsyncSession = Depends(get_db)) -> ScanResponse:
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status not in (ScanStatus.PENDING, ScanStatus.RUNNING):
        raise HTTPException(status_code=400, detail="Scan cannot be cancelled")

    scan.status = ScanStatus.CANCELLED
    await db.commit()
    await db.refresh(scan)

    return ScanResponse(
        id=scan.id,
        target=scan.target,
        scan_type=scan.scan_type.value,
        status=scan.status.value,
        profile=scan.profile,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        created_at=scan.created_at,
    )
