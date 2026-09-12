from __future__ import annotations
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from collections import defaultdict

from app.models.canonical_models import CanonicalTask, NodeType


def _today() -> date:
    return datetime.utcnow().date()


def _parse_iso(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    try:
        return date.fromisoformat(d[:10])
    except Exception:
        return None


def generate_ai_summary(flat_tasks: List[Dict[str, Any]], project_name: str = "") -> Dict[str, Any]:
    today = _today()

    # ── Collect towers, floors, activities ───────────────────────────────────
    towers: set = set()
    floors_by_tower: Dict[str, set] = defaultdict(set)
    activities: List[Dict] = []
    milestones: List[Dict] = []

    for t in flat_tasks:
        node_type = t.get("node_type", "")
        tower = t.get("tower") or "Unknown"
        floor = t.get("floor")
        phase = t.get("phase") or "general"
        discipline = t.get("discipline") or "general"
        planned_start = _parse_iso(t.get("planned_start"))
        planned_finish = _parse_iso(t.get("planned_finish"))
        actual_progress = t.get("actual_progress")
        name = t.get("name", "")

        if node_type == NodeType.stage or node_type == "stage":
            towers.add(tower)
        elif node_type == NodeType.task or node_type == "task":
            if floor:
                floors_by_tower[tower].add(floor)
        elif node_type in (NodeType.sub_task, NodeType.milestone, "sub_task", "milestone"):
            entry = {
                "name": name, "tower": tower, "floor": floor,
                "phase": phase, "discipline": discipline,
                "planned_start": planned_start,
                "planned_finish": planned_finish,
                "actual_progress": actual_progress,
            }
            if node_type in (NodeType.milestone, "milestone"):
                milestones.append(entry)
            else:
                activities.append(entry)

    total_towers = len(towers)
    total_floors = sum(len(f) for f in floors_by_tower.values())
    total_activities = len(activities)
    total_milestones = len(milestones)

    # ── Date analysis ─────────────────────────────────────────────────────────
    all_starts  = [a["planned_start"]  for a in activities if a["planned_start"]]
    all_finishes= [a["planned_finish"] for a in activities if a["planned_finish"]]
    ms_dates    = [m["planned_finish"] for m in milestones  if m["planned_finish"]]

    project_start  = min(all_starts)   if all_starts   else None
    project_finish = max(all_finishes) if all_finishes else None
    duration_days  = (project_finish - project_start).days if project_start and project_finish else None

    # ── Delayed / upcoming ────────────────────────────────────────────────────
    delayed: List[Dict] = []
    upcoming_30: List[Dict] = []
    in_progress_count = 0

    for a in activities + milestones:
        pf = a["planned_finish"]
        ps = a["planned_start"]
        prog = a["actual_progress"]

        is_complete = prog is not None and prog >= 100.0
        if is_complete:
            continue

        if pf and pf < today:
            delayed.append(a)
        elif pf and (pf - today).days <= 30:
            upcoming_30.append(a)

        if ps and ps <= today and (pf is None or pf >= today):
            in_progress_count += 1

    # ── Phase breakdown ───────────────────────────────────────────────────────
    phase_counts: Dict[str, int] = defaultdict(int)
    discipline_counts: Dict[str, int] = defaultdict(int)
    for a in activities:
        phase_counts[a["phase"]] += 1
        discipline_counts[a["discipline"]] += 1

    # ── Tower progress ────────────────────────────────────────────────────────
    tower_stats: Dict[str, Dict] = {}
    for tower in towers:
        t_acts = [a for a in activities if a["tower"] == tower]
        t_floors = len(floors_by_tower.get(tower, set()))
        t_delayed = sum(1 for a in t_acts if a["planned_finish"] and a["planned_finish"] < today
                        and (a["actual_progress"] or 0) < 100)
        t_progs = [a["actual_progress"] for a in t_acts if a["actual_progress"] is not None]
        avg_prog = round(sum(t_progs) / len(t_progs), 1) if t_progs else None

        t_starts  = [a["planned_start"]  for a in t_acts if a["planned_start"]]
        t_finishes= [a["planned_finish"] for a in t_acts if a["planned_finish"]]

        tower_stats[tower] = {
            "tower": tower,
            "floors": t_floors,
            "activities": len(t_acts),
            "delayed": t_delayed,
            "avg_progress": avg_prog,
            "planned_start":  min(t_starts).isoformat()   if t_starts   else None,
            "planned_finish": max(t_finishes).isoformat() if t_finishes else None,
        }

    # ── Critical path: next 5 milestones ──────────────────────────────────────
    upcoming_milestones = sorted(
        [m for m in milestones if m["planned_finish"] and m["planned_finish"] >= today],
        key=lambda m: m["planned_finish"]
    )[:5]

    # ── Risk signals ──────────────────────────────────────────────────────────
    risk_level = "low"
    risk_reasons: List[str] = []

    delayed_pct = len(delayed) / max(total_activities, 1) * 100
    if delayed_pct > 20:
        risk_level = "high"
        risk_reasons.append(f"{len(delayed)} activities ({delayed_pct:.0f}%) are past their planned finish date")
    elif delayed_pct > 5:
        risk_level = "medium"
        risk_reasons.append(f"{len(delayed)} activities are running behind schedule")

    if project_finish and (project_finish - today).days < 30:
        risk_level = "high"
        risk_reasons.append(f"Project completion in {(project_finish - today).days} days")

    if not risk_reasons:
        risk_reasons.append("No major risks detected at this time")

    # ── Natural language narrative ────────────────────────────────────────────
    narrative_lines = []

    narrative_lines.append(
        f"**{project_name or 'This project'}** spans **{total_towers} tower(s)** "
        f"with a total of **{total_floors} floors** and **{total_activities} scheduled activities**."
    )

    if project_start and project_finish:
        narrative_lines.append(
            f"The project runs from **{project_start.strftime('%d %b %Y')}** to "
            f"**{project_finish.strftime('%d %b %Y')}** "
            f"({duration_days} days total)."
        )

    if in_progress_count:
        narrative_lines.append(f"Currently **{in_progress_count} activities** are in progress.")

    if delayed:
        narrative_lines.append(
            f"⚠️ **{len(delayed)} activities** are delayed past their planned completion date."
        )
    else:
        narrative_lines.append("✅ No activities are currently delayed.")

    if upcoming_30:
        narrative_lines.append(
            f"**{len(upcoming_30)} activities** are due within the next 30 days — "
            f"focus recommended on: {', '.join(set(a['phase'] for a in upcoming_30[:3]))}."
        )

    # Top phases
    if phase_counts:
        top_phases = sorted(phase_counts.items(), key=lambda x: -x[1])[:3]
        narrative_lines.append(
            "Primary work phases: " +
            ", ".join(f"**{p.title()}** ({c} activities)" for p, c in top_phases) + "."
        )

    return {
        "summary_text": " ".join(narrative_lines),
        "metrics": {
            "total_towers":      total_towers,
            "total_floors":      total_floors,
            "total_activities":  total_activities,
            "total_milestones":  total_milestones,
            "delayed_count":     len(delayed),
            "delayed_pct":       round(delayed_pct, 1),
            "in_progress_count": in_progress_count,
            "upcoming_30_days":  len(upcoming_30),
            "project_start":     project_start.isoformat()  if project_start  else None,
            "project_finish":    project_finish.isoformat() if project_finish else None,
            "duration_days":     duration_days,
        },
        "risk": {
            "level":   risk_level,
            "reasons": risk_reasons,
        },
        "phase_breakdown": dict(sorted(phase_counts.items(), key=lambda x: -x[1])),
        "discipline_breakdown": dict(sorted(discipline_counts.items(), key=lambda x: -x[1])),
        "tower_stats": list(tower_stats.values()),
        "upcoming_milestones": [
            {
                "name":           m["name"],
                "tower":          m["tower"],
                "floor":          m["floor"],
                "planned_finish": m["planned_finish"].isoformat() if m["planned_finish"] else None,
                "days_away":      (m["planned_finish"] - today).days if m["planned_finish"] else None,
            }
            for m in upcoming_milestones
        ],
        "delayed_activities": [
            {
                "name":           a["name"],
                "tower":          a["tower"],
                "floor":          a["floor"],
                "phase":          a["phase"],
                "planned_finish": a["planned_finish"].isoformat() if a["planned_finish"] else None,
                "days_overdue":   (today - a["planned_finish"]).days if a["planned_finish"] else None,
            }
            for a in sorted(delayed, key=lambda x: x["planned_finish"] or today)[:20]
        ],
    }