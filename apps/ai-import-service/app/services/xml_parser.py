from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any

from lxml import etree


NODE_TYPES_WITH_CHILDREN = {"project", "stage", "summary", "task"}


def parse_xml(file_path: str) -> dict[str, Any]:
    tree = etree.parse(file_path)
    root = tree.getroot()
    tasks = _extract_tasks(root)
    ordered = _topological_like_order(tasks)
    tree_nodes = _build_tree(ordered)
    milestone_count = sum(1 for task in ordered if task["node_type"] == "milestone")
    warnings: list[str] = []

    if not ordered:
        warnings.append("No XML task nodes were found. Check the file format or mapping rules.")

    return {
        "project_name": _project_name(root, ordered),
        "project_type": "general construction",
        "project_type_confidence": 0.58,
        "source_type": "xml",
        "task_count": len(ordered),
        "milestone_count": milestone_count,
        "hierarchy_strategy": "xml-parent-or-outline-level",
        "sheets": [],
        "flat_tasks": ordered,
        "tree": tree_nodes,
        "warnings": warnings,
    }


def _extract_tasks(root: etree._Element) -> list[dict[str, Any]]:
    generic_tasks = [el for el in root.iter() if _local_name(el) in {"Task", "Activity"}]
    if not generic_tasks:
        return []

    raw: list[dict[str, Any]] = []
    for idx, task_el in enumerate(generic_tasks, start=1):
        external_id = _first_text(task_el, ["UID", "TaskUID", "ID", "ObjectId", "ActivityID"]) or f"task-{idx}"
        name = _first_text(task_el, ["Name", "TaskName", "ActivityName", "WBSName"]) or f"Task {idx}"
        explicit_parent = _first_text(task_el, ["ParentTaskUID", "ParentObjectId", "ParentID", "WBSParentObjectId"])
        outline_level = _to_int(_first_text(task_el, ["OutlineLevel", "WBSLevel", "Level"]))
        is_milestone = _to_bool(_first_text(task_el, ["Milestone", "IsMilestone"]))
        duration_days = _duration_days(_first_text(task_el, ["Duration", "RemainingDuration", "OriginalDuration"]))
        planned_start = _to_iso(_first_text(task_el, ["Start", "PlannedStart", "EarlyStart"]))
        planned_finish = _to_iso(_first_text(task_el, ["Finish", "PlannedFinish", "EarlyFinish"]))
        phase = _infer_phase(name)
        tower = _infer_tower(name)
        floor = _infer_floor(name)

        raw.append(
            {
                "external_id": str(external_id),
                "_explicit_parent": str(explicit_parent) if explicit_parent else None,
                "_outline_level": outline_level,
                "source_type": "xml",
                "source_sheet": "XML Import",
                "source_row": idx,
                "name": name.strip(),
                "normalized_name": name.strip(),
                "node_type": _infer_node_type(name, is_milestone, duration_days, outline_level),
                "project_hint": None,
                "tower": tower,
                "block": None,
                "floor": floor,
                "zone": None,
                "phase": phase,
                "discipline": _infer_discipline(name),
                "planned_start": planned_start,
                "planned_finish": planned_finish,
                "actual_start": None,
                "actual_finish": None,
                "actual_progress": None,
                "planned_qty": None,
                "actual_qty": None,
                "uom": None,
                "contractor": None,
                "remarks": None,
                "confidence": 0.82 if explicit_parent or outline_level is not None else 0.64,
            }
        )

    if not any(task["_explicit_parent"] for task in raw):
        _apply_outline_level_parenting(raw)
    else:
        for task in raw:
            task["external_parent_id"] = task.pop("_explicit_parent")
            task.pop("_outline_level", None)

    for task in raw:
        task.pop("_explicit_parent", None)
        task.pop("_outline_level", None)

    return raw


def _apply_outline_level_parenting(tasks: list[dict[str, Any]]) -> None:
    stack: dict[int, str] = {}
    for task in tasks:
        level = task.get("_outline_level") or 1
        parent_id = None
        for candidate_level in range(level - 1, 0, -1):
            if candidate_level in stack:
                parent_id = stack[candidate_level]
                break
        task["external_parent_id"] = parent_id
        stack[level] = task["external_id"]
        for obsolete in [k for k in stack.keys() if k > level]:
            stack.pop(obsolete, None)


def _topological_like_order(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = list(tasks)
    ordered: list[dict[str, Any]] = []
    resolved: set[str] = set()

    while remaining:
        progressed = False
        next_remaining: list[dict[str, Any]] = []
        for task in remaining:
            parent_id = task.get("external_parent_id")
            if parent_id is None or parent_id in resolved or parent_id == task["external_id"]:
                ordered.append(task)
                resolved.add(task["external_id"])
                progressed = True
            else:
                next_remaining.append(task)
        if not progressed:
            ordered.extend(next_remaining)
            break
        remaining = next_remaining

    return ordered


def _build_tree(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {task["external_id"]: {**task, "children": []} for task in tasks}
    roots: list[dict[str, Any]] = []
    for task in tasks:
        current = by_id[task["external_id"]]
        parent_id = task.get("external_parent_id")
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(current)
        else:
            roots.append(current)
    return roots


def _project_name(root: etree._Element, ordered: list[dict[str, Any]]) -> str:
    for candidate in [root.find('.//Name'), root.find('.//ProjectName')]:
        if candidate is not None and candidate.text and candidate.text.strip():
            return candidate.text.strip()
    root_name = _first_text(root, ["Name", "ProjectName", "Title"])
    if root_name:
        return root_name
    if ordered:
        return "Imported XML Project"
    return "Untitled XML Project"


def _first_text(element: etree._Element, names: list[str]) -> str | None:
    normalized = {name.lower() for name in names}
    for child in element.iterchildren():
        if _local_name(child).lower() in normalized:
            if child.text and child.text.strip():
                return child.text.strip()
    return None


def _local_name(element: etree._Element) -> str:
    tag = element.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.split("}", 1)[1]
    return str(tag)


def _to_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _duration_days(value: str | None) -> float | None:
    if not value:
        return None
    stripped = value.strip().lower()
    try:
        return float(stripped)
    except Exception:
        pass
    digits = "".join(ch for ch in stripped if ch.isdigit() or ch == ".")
    if not digits:
        return None
    try:
        return float(digits)
    except Exception:
        return None


def _to_iso(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    for parser in [
        lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).date(),
        lambda s: datetime.strptime(s[:10], "%Y-%m-%d").date(),
        lambda s: datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").date(),
        lambda s: datetime.strptime(s[:10], "%m/%d/%Y").date(),
    ]:
        try:
            return parser(text).isoformat()
        except Exception:
            continue
    return text


def _infer_node_type(name: str, is_milestone: bool, duration_days: float | None, outline_level: int | None) -> str:
    lowered = name.lower()
    if is_milestone or duration_days == 0 or any(word in lowered for word in ["handover", "approval", "complete", "completed"]):
        return "milestone"
    if outline_level is not None:
        if outline_level <= 1:
            return "stage"
        if outline_level == 2:
            return "task"
    return "sub_task"


def _infer_phase(name: str) -> str | None:
    lowered = name.lower()
    keywords = {
        "excavation": ["excavat", "earthwork", "pcc", "footing", "raft"],
        "superstructure": ["column", "beam", "slab", "rcc", "concrete"],
        "mep": ["electrical", "plumbing", "hvac", "fire"],
        "finishing": ["painting", "marble", "flooring", "railing", "tiling", "joinery"],
        "handover": ["handover", "snag", "completion"],
    }
    for phase, terms in keywords.items():
        if any(term in lowered for term in terms):
            return phase
    return None


def _infer_discipline(name: str) -> str | None:
    lowered = name.lower()
    if any(word in lowered for word in ["electrical", "plumbing", "hvac", "fire"]):
        return "mep"
    if any(word in lowered for word in ["paint", "marble", "floor", "tile", "railing"]):
        return "architectural"
    if any(word in lowered for word in ["column", "beam", "slab", "raft", "concrete"]):
        return "civil"
    return None


def _infer_tower(name: str) -> str | None:
    lowered = name.lower().replace(" ", "")
    for prefix in ["towera", "towerb", "towerc", "towerd", "towere", "towerf"]:
        if prefix in lowered:
            return prefix.replace("tower", "Tower ").upper().replace(" ", " ", 1)
    return None


def _infer_floor(name: str) -> str | None:
    tokens = name.replace("-", " ").split()
    for token in tokens:
        normalized = token.lower().strip()
        if normalized.isdigit():
            return normalized
        if normalized.endswith("th") and normalized[:-2].isdigit():
            return normalized[:-2]
    return None
