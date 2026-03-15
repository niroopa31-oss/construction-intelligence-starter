# Task tree + detail panel patch

## What this patch adds
- Angular project overview page backed by live API calls
- Left-side expandable task hierarchy
- Right-side task detail panel with schedule, quantity, discrepancy, and AI suggestion sections
- Spring Boot endpoints for:
  - `GET /api/projects/{projectId}/summary`
  - `GET /api/projects/{projectId}/tasks/tree`
  - `GET /api/projects/{projectId}/tasks/{taskId}/detail`

## Notes
- The backend currently returns placeholder empty arrays for contractor names, documents, images, and discrepancies. Wire those to real tables when you add those modules.
- The status and delayed-day logic is intentionally deterministic so the UI remains stable.
- The Angular page assumes `provideHttpClient()` is already configured.

## Suggested next wiring
1. connect discrepancies/documents/images tables to `TaskTreeService.taskDetail`
2. add inline task progress editing on the detail panel
3. link a plan/image comparison page from the detail panel
