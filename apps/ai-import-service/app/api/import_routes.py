from __future__ import annotations

import os
import tempfile
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.excel_parser import parse_excel
from app.services.xml_parser import parse_xml

router = APIRouter(tags=["imports"])


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
            preview = parse_excel(temp_path, project_name_hint=projectName or None)
        elif suffix == ".xml":
            preview = parse_xml(temp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if projectType:
            preview["project_type"] = projectType
            preview["project_type_confidence"] = 1.0

        return {
            "filename": file.filename,
            "preview": preview,
            "warnings": preview.get("warnings", []),
            "nextStep": "Show mapping and hierarchy review UI, then persist confirmed tasks into core API.",
        }
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
