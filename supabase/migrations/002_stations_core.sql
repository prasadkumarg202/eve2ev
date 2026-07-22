-- ================================================================
-- Master charging database: stations and related entities.
--
-- Applied to project ndxvmzrepgsaxiggkhwy as migrations
-- 20260720185636 (stations_core_schema) and 20260720193118
-- (osm_import_staging). Checked in so the schema is reproducible from
-- the repo rather than living only in the hosted project.
--
-- Column shapes mirror src/lib/types/station.ts so the frontend can read
-- these tables directly, plus provenance columns the multi-source ETL needs.
-- ================================================================

create extension if not exists postgis with schema extensions;
create extension if not exists pg_trgm with schema extensions;

-- ---------- enums ----------
do $$ begin
  create type public.station_status as enum ('available','busy','offline','maintenance');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.charger_status as enum ('available','in_use','offline','maintenance');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.connector_type as enum
    ('CCS2','Type2','BharatAC001','BharatDC001','CHAdeMO','GBT');
exception when duplicate_object then null; end $$;

-- ---------- operators ----------
create table if not exists public.operators (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  logo_url text,
  website text,
  support_phone text,
  support_email text,
  is_partner boolean not null default false,
  created_at timestamptz not null default now()
);

-- ---------- stations ----------
create table if not exists public.stations (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,

  address_line1 text not null default '',
  address_line2 text,
  city text not null default '',
  district text,
  state text not null default '',
  pin_code text,

  -- PostGIS is authoritative; lat/lon are generated so the frontend can read
  -- plain numbers and the two can never drift apart.
  geom extensions.geography(Point, 4326) not null,
  latitude double precision generated always as
    (extensions.st_y(geom::extensions.geometry)) stored,
  longitude double precision generated always as
    (extensions.st_x(geom::extensions.geometry)) stored,

  operator_id uuid references public.operators (id) on delete set null,
  phone text,
  email text,
  opening_hours jsonb,
  is_24x7 boolean not null default false,
  free_parking boolean not null default false,
  is_verified boolean not null default false,

  status public.station_status not null default 'offline',
  avg_rating numeric(2,1) not null default 0,
  review_count integer not null default 0,

  -- ---- provenance / dedupe ----
  data_source text not null default 'seed',
  source_id text,
  -- every source id merged into this row: {"osm":"n123","tata":"TP-99"}
  external_ids jsonb not null default '{}'::jsonb,
  -- which source won each field, for debugging conflicting values
  field_provenance jsonb not null default '{}'::jsonb,
  merge_confidence numeric(3,2),
  -- FK into the osm-india-etl location database
  osm_location_id text,

  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists stations_geom_idx on public.stations using gist (geom);
create index if not exists stations_name_trgm_idx
  on public.stations using gin (name extensions.gin_trgm_ops);
create index if not exists stations_state_city_idx on public.stations (state, city);
create index if not exists stations_status_idx on public.stations (status);
create index if not exists stations_external_ids_idx
  on public.stations using gin (external_ids);
create unique index if not exists stations_source_uniq
  on public.stations (data_source, source_id) where source_id is not null;

-- ---------- chargers ----------
create table if not exists public.chargers (
  id uuid primary key default gen_random_uuid(),
  station_id uuid not null references public.stations (id) on delete cascade,
  connector_type public.connector_type not null,
  power_kw numeric(6,2) not null,
  pricing_model text,
  price_per_kwh numeric(8,2),
  price_per_minute numeric(8,2),
  price_per_session numeric(8,2),
  status public.charger_status not null default 'offline',
  last_status_update timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists chargers_station_id_idx on public.chargers (station_id);
create index if not exists chargers_connector_idx on public.chargers (connector_type);

-- ---------- amenities / photos ----------
create table if not exists public.station_amenities (
  id uuid primary key default gen_random_uuid(),
  station_id uuid not null references public.stations (id) on delete cascade,
  type text not null,
  name text not null,
  distance text,
  icon text not null default ''
);

create index if not exists station_amenities_station_id_idx
  on public.station_amenities (station_id);

create table if not exists public.station_photos (
  id uuid primary key default gen_random_uuid(),
  station_id uuid not null references public.stations (id) on delete cascade,
  url text not null,
  caption text,
  uploaded_by uuid references public.profiles (id) on delete set null,
  created_at timestamptz not null default now()
);

create index if not exists station_photos_station_id_idx
  on public.station_photos (station_id);

-- ---------- import staging ----------
-- Rows land here verbatim, then get promoted. Keeping the raw landing zone
-- lets a bad load be diffed and replayed instead of corrupting the master.
create table if not exists public.import_staging (
  slug text primary key,
  name text,
  city text,
  district text,
  state text,
  pin_code text,
  lon double precision not null,
  lat double precision not null,
  operator_name text,
  operator_slug text,
  source_id text,
  loaded_at timestamptz not null default now()
);

-- ---------- city aliases ----------
-- Indian cities were widely renamed but users search by the older name.
-- Trigram cannot bridge these (Bangalore/Bengaluru scores ~0.2) because they
-- are renames, not misspellings.
create table if not exists public.city_aliases (
  alias      text primary key,
  city_group text not null
);

create index if not exists city_aliases_group_idx on public.city_aliases (city_group);

-- ---------- RLS: public read, writes reserved for the service role ----------
alter table public.operators         enable row level security;
alter table public.stations          enable row level security;
alter table public.chargers          enable row level security;
alter table public.station_amenities enable row level security;
alter table public.station_photos    enable row level security;
alter table public.import_staging    enable row level security;
alter table public.city_aliases      enable row level security;

drop policy if exists "Operators are viewable by everyone" on public.operators;
create policy "Operators are viewable by everyone"
  on public.operators for select using (true);

drop policy if exists "Stations are viewable by everyone" on public.stations;
create policy "Stations are viewable by everyone"
  on public.stations for select using (true);

drop policy if exists "Chargers are viewable by everyone" on public.chargers;
create policy "Chargers are viewable by everyone"
  on public.chargers for select using (true);

drop policy if exists "Amenities are viewable by everyone" on public.station_amenities;
create policy "Amenities are viewable by everyone"
  on public.station_amenities for select using (true);

drop policy if exists "Photos are viewable by everyone" on public.station_photos;
create policy "Photos are viewable by everyone"
  on public.station_photos for select using (true);

drop policy if exists "City aliases are viewable by everyone" on public.city_aliases;
create policy "City aliases are viewable by everyone"
  on public.city_aliases for select using (true);
