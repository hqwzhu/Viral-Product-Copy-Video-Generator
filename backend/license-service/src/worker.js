"use strict";

const path = require("path");
const { createStateStore } = require("./state-store");
const { startHostedWorker } = require("./hosted-worker");
require("dotenv").config();

const stateFile = process.env.LICENSE_SERVICE_STATE_FILE || path.join(__dirname, "..", "var", "license-service-state.json");
const store = createStateStore({ stateFile, databaseUrl: process.env.DATABASE_URL });

store.init().then(async () => {
  await startHostedWorker(store);
  console.log("ENHE Promotion Manager hosted worker started");
}).catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
