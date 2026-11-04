-- ai-versions (Lite): one table that holds every version.
-- Restoring old code in Lovable never touches database rows, so the list survives a restore.
--
-- Who can do what: the app reads and adds versions with the public key, so anyone who has
-- that key can too. These rules limit the damage: a new version must be exactly the next
-- number, texts are short, at most 20 versions a minute, and nobody can change or delete
-- versions from the app. You can still delete rows yourself in the SQL editor.

create table if not exists public.ai_versions (
  version text primary key
    check (version ~ '^v[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}$'),
  entry_hash text not null check (length(entry_hash) between 1 and 64),
  level text not null check (level in ('start', 'patch', 'minor', 'major', 'restore')),
  summary text not null default '' check (length(summary) <= 200),
  note text not null default '' check (length(note) <= 500),
  reason text not null default '' check (length(reason) <= 300),
  restored_from text
    check (restored_from is null or restored_from ~ '^v[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}$'),
  created_at timestamptz not null default now()
);

alter table public.ai_versions enable row level security;

-- Every new row must be the next version after the newest one, so nobody can jump
-- ahead (for example to v999.0.0) and take over the numbering.
create or replace function public.ai_versions_next_only() returns trigger
language plpgsql set search_path = public as $$
declare
  last_version text;
  maj int; mnr int; pat int;
  expected text;
  recent int;
begin
  new.created_at := now();
  select version into last_version from public.ai_versions
    order by split_part(substr(version, 2), '.', 1)::int desc,
             split_part(substr(version, 2), '.', 2)::int desc,
             split_part(substr(version, 2), '.', 3)::int desc
    limit 1;
  if last_version is null then
    expected := 'v1.0.0';
    if new.level <> 'start' then
      raise exception 'ai_versions: the first version must be v1.0.0 (start)';
    end if;
  else
    maj := split_part(substr(last_version, 2), '.', 1)::int;
    mnr := split_part(substr(last_version, 2), '.', 2)::int;
    pat := split_part(substr(last_version, 2), '.', 3)::int;
    expected := case new.level
      when 'patch' then format('v%s.%s.%s', maj, mnr, pat + 1)
      when 'minor' then format('v%s.%s.0', maj, mnr + 1)
      when 'restore' then format('v%s.%s.0', maj, mnr + 1)
      when 'major' then format('v%s.0.0', maj + 1)
      else null
    end;
  end if;
  if expected is null or new.version <> expected then
    raise exception 'ai_versions: % is not the next version (expected %)', new.version, coalesce(expected, 'none');
  end if;
  if new.restored_from is not null
     and not exists (select 1 from public.ai_versions where version = new.restored_from) then
    raise exception 'ai_versions: % does not exist', new.restored_from;
  end if;
  select count(*) into recent from public.ai_versions where created_at > now() - interval '1 minute';
  if recent >= 20 then
    raise exception 'ai_versions: too many new versions in one minute';
  end if;
  return new;
end;
$$;

drop trigger if exists ai_versions_next_only on public.ai_versions;
create trigger ai_versions_next_only
  before insert on public.ai_versions
  for each row execute function public.ai_versions_next_only();

-- The app may read and add versions. There are no update or delete rules,
-- so versions can't be changed or removed from the app.
drop policy if exists "Anyone can read versions" on public.ai_versions;
drop policy if exists "Anyone can add versions" on public.ai_versions;
create policy "Anyone can read versions"
  on public.ai_versions for select using (true);
create policy "Anyone can add versions"
  on public.ai_versions for insert with check (true);
