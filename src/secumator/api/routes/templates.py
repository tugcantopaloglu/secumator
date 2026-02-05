from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Literal
from secumator.core import get_logger, template_manager, ScanTemplate, BUILTIN_TEMPLATES
from secumator.models.scan import ScanType

router = APIRouter()
logger = get_logger("api.templates")


class TemplateResponse(BaseModel):
    name: str
    description: str
    scan_type: str
    rate_limit: int
    timeout: int
    enabled_scanners: list[str]
    tags: list[str]
    is_builtin: bool


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=500)
    scan_type: Literal["webapp", "network", "api", "full"] = "webapp"
    nuclei_templates: list[str] = []
    nuclei_tags: list[str] = []
    nuclei_severity: list[str] = []
    nmap_args: list[str] = []
    nikto_args: list[str] = []
    rate_limit: int = Field(default=150, ge=1, le=1000)
    timeout: int = Field(default=3600, ge=60, le=86400)
    enabled_scanners: list[str] = ["nuclei", "nmap", "nikto"]
    tags: list[str] = []
    options: dict[str, Any] = {}


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    tag: str | None = Query(None, description="Filter by tag"),
    scan_type: str | None = Query(None, description="Filter by scan type"),
):
    if tag:
        templates = template_manager.list_by_tag(tag)
    elif scan_type:
        templates = template_manager.list_by_type(ScanType(scan_type))
    else:
        templates = template_manager.list_all()

    return [
        TemplateResponse(
            name=t.name,
            description=t.description,
            scan_type=t.scan_type.value,
            rate_limit=t.rate_limit,
            timeout=t.timeout,
            enabled_scanners=t.enabled_scanners,
            tags=t.tags,
            is_builtin=t.name in BUILTIN_TEMPLATES,
        )
        for t in templates
    ]


@router.get("/templates/{name}", response_model=dict)
async def get_template(name: str):
    template = template_manager.get(name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "name": template.name,
        "description": template.description,
        "scan_type": template.scan_type.value,
        "options": template.options,
        "nuclei_templates": template.nuclei_templates,
        "nuclei_tags": template.nuclei_tags,
        "nuclei_severity": template.nuclei_severity,
        "nmap_args": template.nmap_args,
        "nikto_args": template.nikto_args,
        "rate_limit": template.rate_limit,
        "timeout": template.timeout,
        "enabled_scanners": template.enabled_scanners,
        "tags": template.tags,
        "is_builtin": template.name in BUILTIN_TEMPLATES,
    }


@router.post("/templates", response_model=dict)
async def create_template(request: TemplateCreateRequest):
    if template_manager.get(request.name):
        raise HTTPException(status_code=409, detail="Template already exists")

    template = ScanTemplate(
        name=request.name,
        description=request.description,
        scan_type=ScanType(request.scan_type),
        options=request.options,
        nuclei_templates=request.nuclei_templates,
        nuclei_tags=request.nuclei_tags,
        nuclei_severity=request.nuclei_severity,
        nmap_args=request.nmap_args,
        nikto_args=request.nikto_args,
        rate_limit=request.rate_limit,
        timeout=request.timeout,
        enabled_scanners=request.enabled_scanners,
        tags=request.tags,
    )

    template_manager.save_custom(template)
    logger.info("template_created", name=request.name)

    return {"status": "created", "name": request.name}


@router.delete("/templates/{name}")
async def delete_template(name: str):
    if name in BUILTIN_TEMPLATES:
        raise HTTPException(status_code=400, detail="Cannot delete built-in templates")

    if not template_manager.get(name):
        raise HTTPException(status_code=404, detail="Template not found")

    success = template_manager.delete_custom(name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete template")

    return {"status": "deleted", "name": name}


@router.get("/templates/{name}/options", response_model=dict)
async def get_template_options(name: str):
    template = template_manager.get(name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template_manager.to_scan_options(template)
