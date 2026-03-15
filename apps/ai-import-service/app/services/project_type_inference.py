from __future__ import annotations

from collections import Counter
from typing import Iterable

from app.models.canonical_models import CanonicalTask

PROJECT_TYPE_KEYWORDS = {
    "high-rise residential": [
        "tower", "floor", "flat", "handover", "balcony", "slab", "sitout", "podium", "lift lobby"
    ],
    "villa project": ["villa", "plot", "clubhouse", "landscape", "compound wall"],
    "interior fit-out": ["fitout", "joinery", "ceiling", "partition", "furniture", "mockup room"],
    "commercial building": ["office", "retail", "mall", "façade", "tenant", "lobby"],
    "industrial project": ["plant", "warehouse", "equipment foundation", "gantry", "utility"],
}


def infer_project_type(filename: str, tasks: Iterable[CanonicalTask]) -> dict:
    scores = Counter()
    joined = " ".join(
        filter(
            None,
            [filename.lower()] + [
                " ".join(
                    filter(None, [
                        (t.name or "").lower(),
                        (t.tower or "").lower(),
                        (t.floor or "").lower(),
                        (t.phase or "").lower(),
                        (t.discipline or "").lower(),
                        (t.remarks or "").lower(),
                    ])
                )
                for t in tasks
            ],
        )
    )
    for project_type, keywords in PROJECT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in joined:
                scores[project_type] += 1

    if not scores:
        return {"projectType": "general construction", "confidence": 0.55}

    project_type, score = scores.most_common(1)[0]
    total = max(sum(scores.values()), 1)
    confidence = min(0.55 + (score / total) * 0.4, 0.96)
    return {"projectType": project_type, "confidence": round(confidence, 2)}
