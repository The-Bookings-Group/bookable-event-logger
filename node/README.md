# @bookable/event-logger (Node.js)

Internal Node.js SDK for publishing Bookable events to Pub/Sub, following the
shared Event Logging Contract.

## Installation

From the `node/` directory:

```bash
npm install
# then in your service, add this repo as a dependency (via Git, GitHub Packages, etc.)
```

## Usage

```js
const { initEventLogger, getEventLogger } = require("./index"); // or @bookable/event-logger

// during startup
initEventLogger(); // uses env vars

// later
const logger = getEventLogger();

logger.info({
  eventType: "email.sync.batch.started",
  correlationId: "req-123",
  data: { accounts_total: 12, sync_type: "cron" },
  actor: { kind: "internal_service", source: "scheduler" },
});

logger.log("warning", {
  eventType: "email.sync.batch.slow",
  correlationId: "req-123",
  data: { duration_ms: 120000 },
});
```

## Environment variables

- `LOG_GCP_PROJECT`
- `LOG_TOPIC` (default: `events`)
- `LOG_ENVIRONMENT`
- `LOG_SERVICE_NAME`
- `LOG_GCP_CREDENTIALS` (path to service account JSON for local/dev)
