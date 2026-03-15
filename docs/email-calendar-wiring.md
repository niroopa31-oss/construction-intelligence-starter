# Real email send + calendar event wiring patch

This patch upgrades task collaboration so reminders can be sent through SMTP and meetings can send real calendar invitations using `.ics` attachments.

## What this patch does

- Sends real reminder emails through `JavaMailSender`
- Sends real meeting invitations by email with `METHOD:REQUEST` calendar attachments
- Tracks reminder send result and meeting invite send time on the task detail panel
- Adds UI actions for:
  - create meeting + optionally send invite now
  - send invite later for an existing meeting
  - create reminder + optionally send now
  - send an existing reminder immediately

## Why this approach

This is the most portable first implementation because recipients on Google Calendar, Outlook, Apple Calendar, and many mobile clients can accept `.ics` invites without forcing you to build OAuth provider integrations first.

## Backend setup

1. Add `spring-boot-starter-mail` to `apps/api-core`
2. Merge `application-email-calendar.yml` into your active Spring config or import it
3. Set these environment variables:

- `MAIL_ENABLED=true`
- `MAIL_USERNAME=...`
- `MAIL_PASSWORD=...`
- `MAIL_FROM_ADDRESS=...`
- `MAIL_FROM_NAME=...`
- `CALENDAR_ORGANIZER_EMAIL=...`
- `CALENDAR_ORGANIZER_NAME=...`
- `CALENDAR_TIMEZONE=America/Toronto`

## API endpoints

- `POST /api/projects/{projectId}/tasks/{taskId}/collaboration/meetings`
- `POST /api/projects/{projectId}/tasks/{taskId}/collaboration/meetings/{meetingId}/send-invite`
- `POST /api/projects/{projectId}/tasks/{taskId}/collaboration/reminders`
- `POST /api/projects/{projectId}/tasks/{taskId}/collaboration/reminders/{reminderId}/send`

## Future upgrade path

Once this is stable, add provider adapters for:
- Google Calendar API for organizer-side event sync
- Microsoft Graph calendar events for organizer-side event sync
- delivery queues for scheduled reminder sending
- Gmail or Outlook specific templates and tracking
