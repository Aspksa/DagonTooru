-- Дракончик Тоору
-- Автор: Матиенко Антон Александрович
-- E-mail: Aspksa@yandex.ru

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('home','work')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('personal','home','work')),
    project_id TEXT REFERENCES projects(id),
    source TEXT NOT NULL DEFAULT 'user',
    status TEXT NOT NULL DEFAULT 'VERIFIED',
    created_at TEXT NOT NULL,
    CHECK ((scope = 'personal' AND project_id IS NULL) OR scope != 'personal')
);

CREATE INDEX IF NOT EXISTS memories_scope_project
    ON memories(scope, project_id, created_at);
