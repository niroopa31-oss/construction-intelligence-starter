# Construction Intelligence Platform Starter

Starter monorepo for a multi-project construction platform that imports Excel/XML, generates project/task hierarchies, and supports reminders, meetings, drawings, images, discrepancies, and AI recommendations.

## Stack
- Angular 20+ frontend
- Spring Boot 3.4+ core API
- FastAPI import + AI service
- PostgreSQL
- MinIO
- RabbitMQ

## Apps
- `apps/web-ui` Angular UI scaffold
- `apps/api-core` Spring Boot business API scaffold
- `apps/ai-import-service` FastAPI import/AI scaffold
- `infra/db/migrations` starter SQL schema

## Run order
1. Start infra: Postgres, MinIO, RabbitMQ
2. Start Spring Boot API
3. Start FastAPI import service
4. Start Angular UI

#Start python server
cd apps/ai-import-service
.venv/bin/uvicorn app.main:app --reload --port 8000

## Core flow
1. User creates/selects project
2. Upload XML or Excel
3. Import service parses and normalizes source
4. Project type is inferred or selected by user
5. Preview hierarchy is shown in UI
6. Confirm import
7. Tasks, milestones, dependencies are stored
8. User attaches drawings/images, schedules meetings, sends reminders
9. Dashboard shows delay/discrepancy/risk summaries


