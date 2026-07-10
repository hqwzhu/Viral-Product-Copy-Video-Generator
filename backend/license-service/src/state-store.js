"use strict";

const fs = require("fs");
const path = require("path");
const { Pool } = require("pg");

const STATE_KEY = "promotion-manager";
const ADVISORY_LOCK_ID = 86420017;

function emptyState() {
  return {
    accounts: {},
    licenses: {},
    subscriptions: {},
    usageLedger: {},
    hostedRuns: {},
    stripeCustomers: {},
    auditLog: []
  };
}

function normalizeState(value) {
  return { ...emptyState(), ...(value && typeof value === "object" ? value : {}) };
}

function createStateStore(options = {}) {
  if (options.databaseUrl || process.env.DATABASE_URL) {
    return new PostgresStateStore(options.databaseUrl || process.env.DATABASE_URL);
  }
  return new JsonStateStore(options.stateFile);
}

class JsonStateStore {
  constructor(stateFile) {
    this.stateFile = stateFile;
  }

  async init() {
    return undefined;
  }

  async load() {
    return loadJsonState(this.stateFile);
  }

  async save(state) {
    saveJsonState(this.stateFile, state);
  }

  async update(mutator) {
    const state = await this.load();
    const result = await mutator(state);
    await this.save(state);
    return result;
  }
}

class PostgresStateStore {
  constructor(databaseUrl) {
    this.pool = new Pool({ connectionString: databaseUrl });
    this.initialized = false;
  }

  async init() {
    if (this.initialized) return;
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS promotion_manager_state (
        state_key text PRIMARY KEY,
        state_json jsonb NOT NULL,
        updated_at timestamptz NOT NULL DEFAULT now()
      )
    `);
    await this.pool.query(
      `INSERT INTO promotion_manager_state (state_key, state_json)
       VALUES ($1, $2::jsonb)
       ON CONFLICT (state_key) DO NOTHING`,
      [STATE_KEY, JSON.stringify(emptyState())]
    );
    this.initialized = true;
  }

  async load() {
    await this.init();
    const result = await this.pool.query(
      "SELECT state_json FROM promotion_manager_state WHERE state_key = $1",
      [STATE_KEY]
    );
    return normalizeState(result.rows[0] && result.rows[0].state_json);
  }

  async save(state) {
    await this.init();
    await this.pool.query(
      `INSERT INTO promotion_manager_state (state_key, state_json, updated_at)
       VALUES ($1, $2::jsonb, now())
       ON CONFLICT (state_key)
       DO UPDATE SET state_json = EXCLUDED.state_json, updated_at = now()`,
      [STATE_KEY, JSON.stringify(normalizeState(state))]
    );
  }

  async update(mutator) {
    await this.init();
    const client = await this.pool.connect();
    try {
      await client.query("BEGIN");
      await client.query("SELECT pg_advisory_xact_lock($1)", [ADVISORY_LOCK_ID]);
      const result = await client.query(
        "SELECT state_json FROM promotion_manager_state WHERE state_key = $1 FOR UPDATE",
        [STATE_KEY]
      );
      const state = normalizeState(result.rows[0] && result.rows[0].state_json);
      const mutationResult = await mutator(state);
      await client.query(
        `INSERT INTO promotion_manager_state (state_key, state_json, updated_at)
         VALUES ($1, $2::jsonb, now())
         ON CONFLICT (state_key)
         DO UPDATE SET state_json = EXCLUDED.state_json, updated_at = now()`,
        [STATE_KEY, JSON.stringify(state)]
      );
      await client.query("COMMIT");
      return mutationResult;
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  async close() {
    await this.pool.end();
  }
}

function loadJsonState(stateFile) {
  if (!fs.existsSync(stateFile)) {
    return emptyState();
  }
  try {
    return normalizeState(JSON.parse(fs.readFileSync(stateFile, "utf8")));
  } catch (_error) {
    return emptyState();
  }
}

function saveJsonState(stateFile, state) {
  fs.mkdirSync(path.dirname(stateFile), { recursive: true });
  fs.writeFileSync(stateFile, `${JSON.stringify(normalizeState(state), null, 2)}\n`);
}

module.exports = {
  ADVISORY_LOCK_ID,
  STATE_KEY,
  JsonStateStore,
  PostgresStateStore,
  createStateStore,
  emptyState,
  loadJsonState,
  normalizeState,
  saveJsonState
};
