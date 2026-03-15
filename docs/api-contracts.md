# API Contracts

## Import Preview
POST `/api/imports/preview`
- multipart/form-data
- file: XML or Excel
- projectType: optional

Response shape:
```json
{
  "filename": "tracker.xlsx",
  "preview": {
    "projectName": "Imported Project",
    "projectType": "high-rise residential",
    "projectTypeConfidence": 0.88,
    "taskCount": 1200,
    "sample": []
  },
  "warnings": [],
  "nextStep": "Show hierarchy preview in UI and allow user to confirm project type/mapping"
}
```

## Project Create
POST `/api/projects`

## Tasks Flat
GET `/api/projects/{projectId}/tasks/flat`
