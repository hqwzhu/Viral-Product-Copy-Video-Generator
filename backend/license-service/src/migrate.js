"use strict";

const { createStateStore } = require("./state-store");
require("dotenv").config();

async function main() {
  if (!process.env.DATABASE_URL) {
    console.log("DATABASE_URL is not set; JSON state fallback needs no migration.");
    return;
  }
  const store = createStateStore({ databaseUrl: process.env.DATABASE_URL });
  await store.init();
  if (store.close) {
    await store.close();
  }
  console.log("Promotion Manager database migration completed.");
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
