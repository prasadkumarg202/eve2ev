-- ================================================================
-- Search, geo and ingest functions.
--
-- Consolidates migrations 20260720185709, 20260720193624, 20260722172019
-- and 20260722191352 into their current (final) definitions.
-- ================================================================

-- ---------------------------------------------------------------- --
-- Radius search. Replaces the in-browser haversine scan, which cannot
-- scale past bundled seed data.
-- ---------------------------------------------------------------- --
create or replace function public.stations_nearby(
  lat double precision,
  lng double precision,
  radius_km double precision default 10,
  max_results integer default 50
)
returns table (
  id uuid, slug text, name text, city text, state text,
  latitude double precision, longitude double precision,
  status public.station_status, avg_rating numeric, review_count integer,
  distance_km double precision
)
language sql
stable
security invoker
set search_path = public, extensions
as $$
  select s.id, s.slug, s.name, s.city, s.state,
         s.latitude, s.longitude, s.status, s.avg_rating, s.review_count,
         extensions.st_distance(
           s.geom, extensions.st_point(lng, lat)::extensions.geography
         ) / 1000.0 as distance_km
  from public.stations s
  where extensions.st_dwithin(
    s.geom, extensions.st_point(lng, lat)::extensions.geography, radius_km * 1000.0
  )
  order by s.geom <-> extensions.st_point(lng, lat)::extensions.geography
  limit greatest(1, least(max_results, 200));
$$;

-- ---------------------------------------------------------------- --
-- Free-text + area search.
--
-- Matches station name, city, district, state, operator or PIN. Two
-- behaviours worth knowing:
--
-- * City aliases are expanded to substring patterns, so "Bombay" finds
--   Mumbai rows and every synonym returns an identical result set.
-- * Trigram thresholds are 0.45 (name/city) and 0.5 (state). Lower values
--   leak across states: similarity('West Bengal','Bengaluru') = 0.38, which
--   made a Bengaluru search return Kolkata. Genuine typos score higher
--   ('karnatka'/'Karnataka' = 0.58) and still match.
-- ---------------------------------------------------------------- --
create or replace function public.stations_search(
  q text default null,
  p_state text default null,
  p_city text default null,
  max_results integer default 50
)
returns table (
  id uuid, slug text, name text, city text, district text, state text,
  pin_code text, latitude double precision, longitude double precision,
  status public.station_status, operator_name text, score real
)
language sql
stable
security invoker
set search_path = public, extensions
as $$
  with needle as (
    select nullif(btrim(coalesce(q, '')), '') as t
  ),
  expanded as (
    select array_agg(distinct '%' || a2.alias || '%') as patterns
    from needle n
    join public.city_aliases a1 on a1.alias = lower(n.t)
    join public.city_aliases a2 on a2.city_group = a1.city_group
  )
  select s.id, s.slug, s.name, s.city, s.district, s.state, s.pin_code,
         s.latitude, s.longitude, s.status, o.name as operator_name,
         case
           when n.t is null then 1.0::real
           when e.patterns is not null
                and (lower(coalesce(s.city, '')) like any (e.patterns)
                  or lower(coalesce(s.district, '')) like any (e.patterns)
                  or lower(coalesce(s.name, '')) like any (e.patterns))
             then 1.0::real
           else greatest(
             extensions.similarity(s.name, n.t),
             extensions.similarity(coalesce(s.city, ''), n.t),
             extensions.similarity(coalesce(s.district, ''), n.t),
             extensions.similarity(coalesce(s.state, ''), n.t),
             extensions.similarity(coalesce(o.name, ''), n.t)
           )
         end as score
  from public.stations s
  cross join needle n
  left join expanded e on true
  left join public.operators o on o.id = s.operator_id
  where (p_state is null or s.state ilike p_state)
    and (p_city  is null or s.city  ilike p_city)
    and (
      n.t is null
      or (e.patterns is not null
          and (lower(coalesce(s.city, '')) like any (e.patterns)
            or lower(coalesce(s.district, '')) like any (e.patterns)
            or lower(coalesce(s.name, '')) like any (e.patterns)))
      or s.pin_code = n.t
      or s.name     ilike '%' || n.t || '%'
      or s.city     ilike '%' || n.t || '%'
      or s.district ilike '%' || n.t || '%'
      or s.state    ilike '%' || n.t || '%'
      or o.name     ilike '%' || n.t || '%'
      or extensions.similarity(s.name, n.t) > 0.45
      or extensions.similarity(coalesce(s.city, ''), n.t) > 0.45
      or extensions.similarity(coalesce(s.state, ''), n.t) > 0.5
    )
  order by score desc, s.name
  limit greatest(1, least(max_results, 200));
$$;

-- ---------------------------------------------------------------- --
-- Distinct areas with stations, for autocomplete / filter dropdowns.
-- ---------------------------------------------------------------- --
create or replace function public.station_areas()
returns table (state text, city text, station_count bigint)
language sql
stable
security invoker
set search_path = public
as $$
  select s.state, nullif(s.city, '') as city, count(*) as station_count
  from public.stations s
  where s.state <> ''
  group by s.state, nullif(s.city, '')
  order by count(*) desc;
$$;

-- ---------------------------------------------------------------- --
-- Bulk upsert entry point for ETL connectors.
--
-- Takes a jsonb array of canonical stations, resolves operators, builds
-- PostGIS geography and upserts in one round trip - so connectors never
-- have to speak WKT. SECURITY DEFINER with EXECUTE revoked from anon and
-- authenticated: only the service role may write to the master table.
-- ---------------------------------------------------------------- --
create or replace function public.import_stations(payload jsonb)
returns table (inserted integer, updated integer, operators_added integer)
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_ops_before integer; v_ops_after integer;
  v_before integer; v_after integer; v_updated integer;
begin
  select count(*) into v_ops_before from public.operators;
  select count(*) into v_before     from public.stations;

  insert into public.operators (name, slug)
  select distinct on (e->>'operator_slug')
         e->>'operator_name', e->>'operator_slug'
  from jsonb_array_elements(payload) e
  where nullif(e->>'operator_slug', '') is not null
  order by e->>'operator_slug', length(e->>'operator_name') desc
  on conflict (slug) do nothing;

  with incoming as (
    select e->>'slug' as slug,
           coalesce(e->>'name', 'Charging Station') as name,
           coalesce(e->>'city', '') as city,
           nullif(e->>'district', '') as district,
           coalesce(e->>'state', '') as state,
           nullif(e->>'pin_code', '') as pin_code,
           (e->>'lon')::double precision as lon,
           (e->>'lat')::double precision as lat,
           nullif(e->>'operator_slug', '') as operator_slug,
           nullif(e->>'source_id', '') as source_id,
           coalesce(e->'external_ids', '{}'::jsonb) as external_ids,
           coalesce(e->>'data_source', 'osm') as data_source
    from jsonb_array_elements(payload) e
    where e->>'slug' is not null
      and (e->>'lat') is not null
      and (e->>'lon') is not null
  )
  insert into public.stations
    (slug, name, city, district, state, pin_code, geom, operator_id,
     data_source, source_id, external_ids, status)
  select i.slug, i.name, i.city, i.district, i.state, i.pin_code,
         extensions.st_point(i.lon, i.lat)::extensions.geography,
         o.id, i.data_source, i.source_id, i.external_ids, 'available'
  from incoming i
  left join public.operators o on o.slug = i.operator_slug
  on conflict (slug) do update
    set name        = excluded.name,
        city        = case when excluded.city <> '' then excluded.city else public.stations.city end,
        district    = coalesce(excluded.district, public.stations.district),
        state       = case when excluded.state <> '' then excluded.state else public.stations.state end,
        pin_code    = coalesce(excluded.pin_code, public.stations.pin_code),
        geom        = excluded.geom,
        operator_id = coalesce(excluded.operator_id, public.stations.operator_id),
        -- merge id maps rather than overwriting: a station known to several
        -- sources must keep every id across loads
        external_ids = public.stations.external_ids || excluded.external_ids,
        updated_at   = now();

  get diagnostics v_updated = row_count;
  select count(*) into v_after     from public.stations;
  select count(*) into v_ops_after from public.operators;

  return query select (v_after - v_before)::integer,
                      (v_updated - (v_after - v_before))::integer,
                      (v_ops_after - v_ops_before)::integer;
end;
$$;

revoke execute on function public.import_stations(jsonb) from public;
revoke execute on function public.import_stations(jsonb) from anon;
revoke execute on function public.import_stations(jsonb) from authenticated;

-- ---------------------------------------------------------------- --
-- Keep updated_at honest on station writes.
-- ---------------------------------------------------------------- --
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists stations_touch_updated_at on public.stations;
create trigger stations_touch_updated_at
  before update on public.stations
  for each row execute function public.touch_updated_at();

-- ---------------------------------------------------------------- --
-- handle_new_user() runs SECURITY DEFINER from the on_auth_user_created
-- trigger only. Leaving EXECUTE granted to PUBLIC exposed it as an RPC
-- endpoint to anon and authenticated roles (migration 20260720181215).
-- ---------------------------------------------------------------- --
revoke execute on function public.handle_new_user() from public;
revoke execute on function public.handle_new_user() from anon;
revoke execute on function public.handle_new_user() from authenticated;
