CREATE TABLE IF NOT EXISTS promotion_manager_state (
  state_key text PRIMARY KEY,
  state_json jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO promotion_manager_state (state_key, state_json)
VALUES ('promotion-manager', '{
  "accounts": {},
  "licenses": {},
  "subscriptions": {},
  "usageLedger": {},
  "hostedRuns": {},
  "stripeCustomers": {},
  "auditLog": []
}'::jsonb)
ON CONFLICT (state_key) DO NOTHING;
