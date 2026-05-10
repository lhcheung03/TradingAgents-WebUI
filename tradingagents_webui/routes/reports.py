"""Reports routes - list, load, and manage saved reports."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
from pathlib import Path
import json


router = APIRouter(prefix="/api/reports", tags=["reports"])

_REPORTS_DIR = Path.home() / ".tradingagents" / "reports"
_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("")
async def list_reports():
    """List all saved reports."""
    reports = []
    for meta_file in _REPORTS_DIR.glob("*_meta.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            reports.append(metadata)
        except Exception:
            continue

    reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return JSONResponse({"reports": reports})


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Get a specific report by ID."""
    filepath = _REPORTS_DIR / f"{report_id}.md"
    meta_filepath = _REPORTS_DIR / f"{report_id}_meta.json"

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    metadata = {}
    if meta_filepath.exists():
        with open(meta_filepath, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    return JSONResponse(
        {"report_id": report_id, "content": content, "metadata": metadata}
    )


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """Delete a report."""
    md_file = _REPORTS_DIR / f"{report_id}.md"
    meta_file = _REPORTS_DIR / f"{report_id}_meta.json"

    deleted = False
    if md_file.exists():
        md_file.unlink()
        deleted = True
    if meta_file.exists():
        meta_file.unlink()

    if not deleted:
        raise HTTPException(
            status_code=404, detail="Report not found or already deleted"
        )

    return JSONResponse({"status": "deleted", "report_id": report_id})
