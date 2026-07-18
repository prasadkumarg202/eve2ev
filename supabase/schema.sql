-- ================================================================
-- Ev2Ev — Supabase schema
-- Run in the Supabase SQL editor (or `supabase db push`) to provision
-- the tables the app reads/writes. Safe to run on a fresh project.
-- ================================================================

-- ---------- profiles ----------
-- One row per auth user. Auto-created by a trigger on signup.
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null default 'EV Driver',
  avatar_url text,
  role text not null default 'user',
  preferred_language text not null default 'en',
  reward_points integer not null default 0,
  reward_tier text not null default 'bronze',
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

drop policy if exists "Profiles are viewable by everyone" on public.profiles;
create policy "Profiles are viewable by everyone"
  on public.profiles for select using (true);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
  on public.profiles for update using (auth.uid() = id);

drop policy if exists "Users can insert own profile" on public.profiles;
create policy "Users can insert own profile"
  on public.profiles for insert with check (auth.uid() = id);

-- Auto-create a profile row when a new auth user signs up.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, display_name, avatar_url)
  values (
    new.id,
    coalesce(
      new.raw_user_meta_data ->> 'full_name',
      new.raw_user_meta_data ->> 'name',
      split_part(new.email, '@', 1),
      'EV Driver'
    ),
    new.raw_user_meta_data ->> 'avatar_url'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------- reviews ----------
-- Stations live in bundled seed data (not the DB yet), so reviews key on
-- the station slug rather than a stations FK.
create table if not exists public.reviews (
  id uuid primary key default gen_random_uuid (),
  user_id uuid not null references public.profiles (id) on delete cascade,
  station_slug text not null,
  rating integer not null check (rating between 1 and 5),
  body text not null,
  waiting_minutes integer,
  status text not null default 'approved',
  created_at timestamptz not null default now()
);

create index if not exists reviews_station_slug_idx on public.reviews (station_slug);
create unique index if not exists reviews_user_station_uniq
  on public.reviews (user_id, station_slug);

alter table public.reviews enable row level security;

drop policy if exists "Approved reviews are viewable by everyone" on public.reviews;
create policy "Approved reviews are viewable by everyone"
  on public.reviews for select using (status = 'approved' or auth.uid() = user_id);

drop policy if exists "Users can create own reviews" on public.reviews;
create policy "Users can create own reviews"
  on public.reviews for insert with check (auth.uid() = user_id);

drop policy if exists "Users can update own reviews" on public.reviews;
create policy "Users can update own reviews"
  on public.reviews for update using (auth.uid() = user_id);

drop policy if exists "Users can delete own reviews" on public.reviews;
create policy "Users can delete own reviews"
  on public.reviews for delete using (auth.uid() = user_id);

-- ---------- favorites ----------
create table if not exists public.favorites (
  user_id uuid not null references public.profiles (id) on delete cascade,
  station_slug text not null,
  created_at timestamptz not null default now(),
  primary key (user_id, station_slug)
);

alter table public.favorites enable row level security;

drop policy if exists "Users can view own favorites" on public.favorites;
create policy "Users can view own favorites"
  on public.favorites for select using (auth.uid() = user_id);

drop policy if exists "Users can add own favorites" on public.favorites;
create policy "Users can add own favorites"
  on public.favorites for insert with check (auth.uid() = user_id);

drop policy if exists "Users can remove own favorites" on public.favorites;
create policy "Users can remove own favorites"
  on public.favorites for delete using (auth.uid() = user_id);

-- ---------- bookings ----------
create table if not exists public.bookings (
  id uuid primary key default gen_random_uuid (),
  user_id uuid not null references public.profiles (id) on delete cascade,
  station_slug text not null,
  charger_id text,
  slot_start timestamptz not null,
  slot_end timestamptz not null,
  status text not null default 'confirmed',
  qr_code text,
  created_at timestamptz not null default now()
);

create index if not exists bookings_user_id_idx on public.bookings (user_id);

alter table public.bookings enable row level security;

drop policy if exists "Users can view own bookings" on public.bookings;
create policy "Users can view own bookings"
  on public.bookings for select using (auth.uid() = user_id);

drop policy if exists "Users can create own bookings" on public.bookings;
create policy "Users can create own bookings"
  on public.bookings for insert with check (auth.uid() = user_id);

drop policy if exists "Users can update own bookings" on public.bookings;
create policy "Users can update own bookings"
  on public.bookings for update using (auth.uid() = user_id);
