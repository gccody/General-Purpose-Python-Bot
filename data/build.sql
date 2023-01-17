CREATE TABLE IF NOT EXISTS bans (
    guild_id TEXT,
    user_id TEXT,
    mod_id TEXT,
    reason TEXT,
    ts INTEGER
);

CREATE TABLE IF NOT EXISTS guilds (
    id text PRIMARY KEY,
    a_id TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    guild_id TEXT,
    user_id TEXT,
    target_id TEXT,
    report TEXT
);

CREATE TABLE IF NOT EXISTS commands (
    command_name TEXT,
    guild_id TEXT,
    user_id TEXT,
    params JSON,
    ts INTEGER
);