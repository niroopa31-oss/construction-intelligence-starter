create table import_draft (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references app_user(id),
  file_name varchar(500),
  source_type varchar(50) not null,
  project_name varchar(255) not null,
  project_type_suggested varchar(100),
  project_type_selected varchar(100),
  status varchar(50) not null default 'draft',
  created_at timestamp not null default now()
);

create table import_draft_node (
  id uuid primary key default gen_random_uuid(),
  draft_id uuid not null references import_draft(id) on delete cascade,
  parent_id uuid references import_draft_node(id),
  external_source_id varchar(255),
  name varchar(500) not null,
  node_type varchar(50) not null,
  phase varchar(100),
  discipline varchar(100),
  tower varchar(100),
  block_name varchar(100),
  floor_name varchar(100),
  zone_name varchar(100),
  baseline_start date,
  baseline_finish date,
  planned_qty numeric(18,3),
  uom varchar(50),
  confidence_score numeric(5,2),
  sort_order int not null default 0
);
