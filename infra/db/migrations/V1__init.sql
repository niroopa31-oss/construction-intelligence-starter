create extension if not exists pgcrypto;

create table app_user (
  id uuid primary key default gen_random_uuid(),
  email varchar(255) not null unique,
  full_name varchar(255),
  created_at timestamp not null default now()
);

create table project (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references app_user(id),
  name varchar(255) not null,
  project_type varchar(100) not null,
  source_type varchar(50) not null,
  location varchar(255),
  baseline_start date,
  baseline_finish date,
  forecast_finish date,
  status varchar(50) not null default 'draft',
  created_at timestamp not null default now()
);

create table task (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references project(id),
  parent_id uuid references task(id),
  external_source_id varchar(255),
  external_parent_id varchar(255),
  name varchar(500) not null,
  normalized_name varchar(500),
  node_type varchar(50) not null,
  phase varchar(100),
  discipline varchar(100),
  tower varchar(100),
  block_name varchar(100),
  floor_name varchar(100),
  zone_name varchar(100),
  baseline_start date,
  baseline_finish date,
  actual_start date,
  actual_finish date,
  forecast_finish date,
  planned_qty numeric(18,3),
  actual_qty numeric(18,3),
  uom varchar(50),
  progress_percent numeric(5,2),
  critical_flag boolean not null default false,
  confidence_score numeric(5,2),
  created_at timestamp not null default now()
);

create table task_dependency (
  id uuid primary key default gen_random_uuid(),
  predecessor_task_id uuid not null references task(id),
  successor_task_id uuid not null references task(id),
  relation_type varchar(20) not null default 'FS'
);

create table contractor (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references project(id),
  company_name varchar(255) not null,
  contact_name varchar(255),
  email varchar(255),
  phone varchar(50),
  trade_type varchar(100)
);

create table task_assignment (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references task(id),
  contractor_id uuid not null references contractor(id),
  role_name varchar(100)
);

create table task_document (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references task(id),
  file_name varchar(255) not null,
  file_type varchar(50) not null,
  file_path varchar(1000) not null,
  version_no int not null default 1,
  drawing_sheet varchar(100),
  zone_tag varchar(100),
  uploaded_at timestamp not null default now()
);

create table task_image (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references task(id),
  file_path varchar(1000) not null,
  floor_name varchar(100),
  zone_name varchar(100),
  ai_summary text,
  ai_progress_estimate numeric(5,2),
  uploaded_at timestamp not null default now()
);

create table discrepancy (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references task(id),
  discrepancy_type varchar(100) not null,
  severity varchar(20) not null,
  source varchar(50) not null,
  summary text,
  recommendation text,
  status varchar(50) not null default 'open',
  created_at timestamp not null default now()
);

create table meeting (
  id uuid primary key default gen_random_uuid(),
  task_id uuid references task(id),
  title varchar(255) not null,
  agenda text,
  start_time timestamp,
  end_time timestamp,
  status varchar(50) not null default 'scheduled',
  created_at timestamp not null default now()
);

create table reminder (
  id uuid primary key default gen_random_uuid(),
  task_id uuid references task(id),
  subject varchar(255),
  body text,
  recipients text,
  scheduled_at timestamp,
  sent_at timestamp,
  status varchar(50) not null default 'draft',
  created_at timestamp not null default now()
);
