create table task_meeting (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references task(id),
  title varchar(255) not null,
  agenda text,
  start_time timestamp,
  end_time timestamp,
  attendees text,
  status varchar(50) not null default 'scheduled',
  calendar_event_uid varchar(255),
  calendar_sequence integer default 0,
  invite_sent_at timestamp,
  created_at timestamp not null default now()
);

create table task_reminder (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references task(id),
  subject varchar(255),
  body text,
  recipients text,
  scheduled_at timestamp,
  sent_at timestamp,
  status varchar(50) not null default 'draft',
  send_error text,
  created_at timestamp not null default now()
);

alter table task_assignment add column if not exists created_at timestamp not null default now();
