create table parcels (
  id text primary key,
  user_id uuid references auth.users(id) on delete cascade,
  name text,
  geom jsonb,
  ai_insight jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now())
);