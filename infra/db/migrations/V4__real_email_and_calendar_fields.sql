alter table task_meeting add column if not exists calendar_event_uid varchar(255);
alter table task_meeting add column if not exists calendar_sequence integer default 0;
alter table task_meeting add column if not exists invite_sent_at timestamp;

alter table task_reminder add column if not exists send_error text;
