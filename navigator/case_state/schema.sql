-- Case State schema v0.1 (owner: Silver). SQLite, Python standard library only (sqlite3).
-- One Case = one person's situation. Every change creates a new case_version; nothing is overwritten in place.
-- Privacy: location is ZIP or county only. No SSN, date of birth, ID, bank or card numbers (contracts S9).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cases (
    case_id         TEXT PRIMARY KEY,                 -- anonymous sessions use the session id
    created_at      TEXT NOT NULL,                    -- ISO 8601
    updated_at      TEXT NOT NULL,
    current_version INTEGER NOT NULL DEFAULT 1 CHECK (current_version >= 1),
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    locale          TEXT NOT NULL DEFAULT 'en-US',
    account_id      TEXT                              -- NULL = anonymous (accounts are optional, P1)
);

-- What the person told us, and what they confirmed. A changed fact is a new row; the old row becomes superseded.
CREATE TABLE IF NOT EXISTS case_facts (
    row_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id             TEXT NOT NULL REFERENCES cases(case_id),
    case_version        INTEGER NOT NULL,
    fact_id             TEXT NOT NULL,
    field               TEXT NOT NULL,                -- e.g. zip_code, household_size, rent_due_date
    value_json          TEXT,                         -- JSON; NULL = unknown (never 0 or false)
    confirmation_status TEXT NOT NULL CHECK (confirmation_status IN ('proposed', 'confirmed', 'disputed', 'superseded')),
    source              TEXT NOT NULL CHECK (source IN ('user_statement', 'user_confirmed', 'system_derived')),
    time_context        TEXT,
    created_at          TEXT NOT NULL
);

-- The person's needs: the top layer of the plan (needs first, actions second).
CREATE TABLE IF NOT EXISTS needs (
    row_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id             TEXT NOT NULL REFERENCES cases(case_id),
    case_version        INTEGER NOT NULL,
    need_id             TEXT NOT NULL,
    category            TEXT NOT NULL,
    subcategory         TEXT,
    description         TEXT NOT NULL,
    original_quote      TEXT,
    confirmation_status TEXT NOT NULL CHECK (confirmation_status IN ('proposed', 'confirmed', 'disputed', 'superseded')),
    urgency             TEXT NOT NULL CHECK (urgency IN ('immediate', 'high', 'normal', 'unknown')),
    urgency_reason      TEXT,
    user_priority       INTEGER,                      -- set only by the user
    UNIQUE (case_id, case_version, need_id)
);

-- Questions we asked and the answers (a skipped answer stays unknown).
CREATE TABLE IF NOT EXISTS clarifications (
    row_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id       TEXT NOT NULL REFERENCES cases(case_id),
    case_version  INTEGER NOT NULL,
    fact_key      TEXT NOT NULL,
    question      TEXT NOT NULL,
    asked_at      TEXT NOT NULL,
    answer_json   TEXT,
    answered_at   TEXT,
    skipped       INTEGER NOT NULL DEFAULT 0 CHECK (skipped IN (0, 1))
);

-- Every plan we released, kept as delivered (plan_json) plus a needs-first index below.
CREATE TABLE IF NOT EXISTS plan_versions (
    plan_id         TEXT PRIMARY KEY,
    case_id         TEXT NOT NULL REFERENCES cases(case_id),
    case_version    INTEGER NOT NULL,
    plan_version    INTEGER NOT NULL,
    created_at      TEXT NOT NULL,
    verdict         TEXT NOT NULL CHECK (verdict IN ('PASS', 'FLAG')),   -- Agent 10
    released        INTEGER NOT NULL CHECK (released IN (0, 1)),
    plan_json       TEXT NOT NULL,
    UNIQUE (case_id, plan_version)
);

-- Needs layer of each plan: which needs, in what order, with what urgency.
CREATE TABLE IF NOT EXISTS plan_needs (
    plan_id    TEXT NOT NULL REFERENCES plan_versions(plan_id),
    need_id    TEXT NOT NULL,
    need_rank  INTEGER NOT NULL,
    urgency    TEXT NOT NULL,
    PRIMARY KEY (plan_id, need_id)
);

-- Action cards of each plan, and which needs each card serves.
CREATE TABLE IF NOT EXISTS action_cards (
    plan_id         TEXT NOT NULL REFERENCES plan_versions(plan_id),
    card_id         TEXT NOT NULL,
    program_id      TEXT,
    action_title    TEXT NOT NULL,
    order_group     TEXT CHECK (order_group IN ('first', 'parallel', 'later')),
    official_deadline TEXT,
    user_target_date  TEXT,
    PRIMARY KEY (plan_id, card_id)
);
CREATE TABLE IF NOT EXISTS card_needs (
    plan_id  TEXT NOT NULL,
    card_id  TEXT NOT NULL,
    need_id  TEXT NOT NULL,
    PRIMARY KEY (plan_id, card_id, need_id),
    FOREIGN KEY (plan_id, card_id) REFERENCES action_cards(plan_id, card_id)
);

-- Progress the USER sets on a card. Agents never write here.
CREATE TABLE IF NOT EXISTS card_status (
    case_id     TEXT NOT NULL REFERENCES cases(case_id),
    card_id     TEXT NOT NULL,
    status      TEXT NOT NULL,                        -- allowed values: store.PROGRESS_STATUSES
    note        TEXT,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (case_id, card_id)
);

-- History: append-only log of everything that changed.
CREATE TABLE IF NOT EXISTS events (
    event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id      TEXT NOT NULL REFERENCES cases(case_id),
    at           TEXT NOT NULL,
    actor        TEXT NOT NULL,                       -- 'user', 'supervisor', or an agent id
    event_type   TEXT NOT NULL,                       -- case_created, fact_added, plan_released, status_changed, ...
    case_version INTEGER NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
