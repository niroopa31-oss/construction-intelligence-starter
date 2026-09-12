from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.services.excel_parser import ExcelNormalizationService   # ← change import
from app.services.xml_parser import parse_xml

router = APIRouter(tags=["imports"])
_excel_svc = ExcelNormalizationService()                           # ← singleton


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/imports/preview")
async def preview_import(
    file: UploadFile = File(...),
    projectType: str = Form(default=""),
    projectName: str = Form(default=""),
):
    suffix = os.path.splitext(file.filename or "")[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name

    try:
        if suffix in [".xlsx", ".xlsm", ".xls"]:
            preview = _excel_svc.parse_workbook(            # ← use ExcelNormalizationService
                temp_path,
                project_name_hint=projectName or None
            )
            result = preview.model_dump()                   # pydantic → dict
        elif suffix == ".xml":
            result = parse_xml(temp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if projectType:
            result["project_type"] = projectType
            result["project_type_confidence"] = 1.0

        return {
            "filename": file.filename,
            "preview": result,
            "warnings": result.get("warnings", []),
            "nextStep": "Show mapping and hierarchy review UI, then persist confirmed tasks into core API.",
        }
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@router.post("/projects/{project_id}/ai-summary")
async def get_ai_summary(project_id: str, payload: dict):
    """
    Generate AI summary from flat_tasks already parsed.
    Expects body: { "flat_tasks": [...], "project_name": "..." }
    """
    flat_tasks = payload.get("flat_tasks", [])
    project_name = payload.get("project_name", "")

    if not flat_tasks:
        raise HTTPException(status_code=400, detail="flat_tasks is required")

    summary = generate_ai_summary(flat_tasks, project_name=project_name)
    return summary


@router.post("/projects/{project_id}/import-with-status")
async def import_with_status(project_id: str, file: UploadFile = File(...)):
    """Import Excel file and extract task status from cell colors."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        tasks = parse_excel_with_colors(tmp_path)
        return {
            "project_id": project_id,
            "task_count": len(tasks),
            "tasks": tasks
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def get_cell_status(cell) -> str:
    """Map cell background color to task status."""
    fill = cell.fill
    if fill and fill.fgColor and fill.fgColor.type == "rgb":
        rgb = fill.fgColor.rgb.upper()
        if any(rgb.startswith(g) for g in ["FF00B050", "FF92D050", "FF00FF00", "FF70AD47"]):
            return "completed"
        if any(rgb.startswith(y) for y in ["FFFFFF00", "FFFFEB9C", "FFFFC000", "FFFFEB84"]):
            return "in_progress"
        if any(rgb.startswith(r) for r in ["FFFF0000", "FFFF5050", "FFFF4040", "FFFF4B4B"]):
            return "overdue"
    return "not_started"


def parse_excel_with_colors(file_path: str) -> list[dict]:
    wb = load_workbook(file_path, data_only=True)
    ws = wb.active

    tasks = []
    header_row = 3
    headers = [ws.cell(row=header_row, column=c).value for c in range(1, ws.max_column + 1)]

    for row_idx in range(header_row + 1, ws.max_row + 1):
        row_data = {}
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            value = cell.value
            status = get_cell_status(cell)
            if header:
                row_data[str(header)] = {
                    "value": str(value) if value else None,
                    "status": status
                }
        if any(v["value"] for v in row_data.values()):
            tasks.append(row_data)

    return tasks
