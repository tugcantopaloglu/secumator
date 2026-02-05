from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from secumator.core.database import get_db
from secumator.models.scan import Scan, Finding

router = APIRouter()


@router.get("/stats/dashboard")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    total_scans = await db.scalar(select(func.count(Scan.id)))
    
    scans_this_week = await db.scalar(
        select(func.count(Scan.id)).where(Scan.created_at >= week_ago)
    )
    
    scans_this_month = await db.scalar(
        select(func.count(Scan.id)).where(Scan.created_at >= month_ago)
    )
    
    total_findings = await db.scalar(select(func.count(Finding.id)))
    
    severity_counts = {}
    for severity in ["critical", "high", "medium", "low", "info"]:
        count = await db.scalar(
            select(func.count(Finding.id)).where(Finding.severity == severity)
        )
        severity_counts[severity] = count or 0
    
    status_counts = {}
    for status in ["pending", "running", "completed", "failed", "cancelled"]:
        count = await db.scalar(
            select(func.count(Scan.id)).where(Scan.status == status)
        )
        status_counts[status] = count or 0
    
    recent_scans = await db.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(10)
    )
    recent_scan_list = [
        {
            "id": s.id,
            "target": s.target,
            "status": s.status,
            "scan_type": s.scan_type,
            "created_at": s.created_at.isoformat(),
        }
        for s in recent_scans.scalars()
    ]
    
    return {
        "overview": {
            "total_scans": total_scans or 0,
            "scans_this_week": scans_this_week or 0,
            "scans_this_month": scans_this_month or 0,
            "total_findings": total_findings or 0,
        },
        "severity_distribution": severity_counts,
        "scan_status": status_counts,
        "recent_scans": recent_scan_list,
    }


@router.get("/stats/trends")
async def get_trends(days: int = 30, db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    scans_by_day = []
    findings_by_day = []
    
    for i in range(days):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        scan_count = await db.scalar(
            select(func.count(Scan.id)).where(
                Scan.created_at >= day_start,
                Scan.created_at < day_end
            )
        )
        
        finding_count = await db.scalar(
            select(func.count(Finding.id)).where(
                Finding.created_at >= day_start,
                Finding.created_at < day_end
            )
        )
        
        scans_by_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": scan_count or 0,
        })
        
        findings_by_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": finding_count or 0,
        })
    
    severity_trend = []
    for severity in ["critical", "high", "medium", "low"]:
        count = await db.scalar(
            select(func.count(Finding.id)).where(
                Finding.severity == severity,
                Finding.created_at >= start_date
            )
        )
        severity_trend.append({"severity": severity, "count": count or 0})
    
    return {
        "period_days": days,
        "scans_by_day": scans_by_day,
        "findings_by_day": findings_by_day,
        "severity_trend": severity_trend,
    }


@router.get("/stats/top-vulnerabilities")
async def get_top_vulnerabilities(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Finding.title, func.count(Finding.id).label("count"))
        .group_by(Finding.title)
        .order_by(func.count(Finding.id).desc())
        .limit(limit)
    )
    
    top_vulns = [{"title": row[0], "count": row[1]} for row in result.all()]
    
    result = await db.execute(
        select(Finding.affected_component, func.count(Finding.id).label("count"))
        .where(Finding.affected_component.isnot(None))
        .group_by(Finding.affected_component)
        .order_by(func.count(Finding.id).desc())
        .limit(limit)
    )
    
    top_components = [{"component": row[0], "count": row[1]} for row in result.all()]
    
    return {
        "top_vulnerabilities": top_vulns,
        "most_affected_components": top_components,
    }
